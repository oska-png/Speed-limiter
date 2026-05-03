import tkinter as tk
import math
import serial
import serial.tools.list_ports
import threading

# Параметры окна
WIDTH = 900
HEIGHT = 500
MAX_SPEED = 200
MAX_RPM = 8000

# Цвета
BG_COLOR = "#f0f0f0"
FG_COLOR = "#000000"
NEEDLE_COLOR = "#ff3333"
TICK_COLOR = "#666666"
RED_TICK_COLOR = "#ff3333"
OUTLINE_COLOR = "#000000"

# Глобальные данные
current_speed = 0.0
speed_limit = 60
serial_connected = False

def find_arduino_port():
    """Автоматически ищет Arduino по описанию 'Arduino' или 'CH340'."""
    ports = serial.tools.list_ports.comports()
    for port, desc, hwid in ports:
        if "Arduino" in desc or "CH340" in desc:
            print(f"Arduino найден на порту: {port} (Описание: {desc})")
            return port
    print("Arduino не найден. Проверьте подключение.")
    return None

def angle_for_value(value, max_val):
    """Преобразует значение в угол от -135° до +135°"""
    fraction = min(max(value / max_val, 0), 1)
    angle_deg = -135 + fraction * 270
    return math.radians(angle_deg)

def draw_dial(canvas, x, y, radius, value, max_val, title, tick_step, red_threshold=None):
    """Рисует круглый прибор"""
    # Внешний круг
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                       outline=OUTLINE_COLOR, width=2, fill=BG_COLOR)

    # Метки и цифры
    for val in range(0, max_val + 1, tick_step):
        angle = angle_for_value(val, max_val)
        x_inner = x + (radius - 10) * math.cos(angle)
        y_inner = y + (radius - 10) * math.sin(angle)
        x_outer = x + radius * math.cos(angle)
        y_outer = y + radius * math.sin(angle)
        tick_color = RED_TICK_COLOR if (red_threshold and val >= red_threshold) else TICK_COLOR
        canvas.create_line(x_inner, y_inner, x_outer, y_outer, fill=tick_color, width=1)

        x_text = x + (radius - 25) * math.cos(angle)
        y_text = y + (radius - 25) * math.sin(angle)
        text_color = RED_TICK_COLOR if (red_threshold and val >= red_threshold) else FG_COLOR
        canvas.create_text(x_text, y_text, text=str(val), fill=text_color, font=("Arial", 9))

    # Стрелка
    needle_angle = angle_for_value(value, max_val)
    needle_len = radius - 20
    needle_x = x + needle_len * math.cos(needle_angle)
    needle_y = y + needle_len * math.sin(needle_angle)
    canvas.create_line(x, y, needle_x, needle_y, fill=NEEDLE_COLOR, width=3)

    # Центральный кружок
    canvas.create_oval(x - 6, y - 6, x + 6, y + 6, fill=FG_COLOR, outline="")

    # Подпись
    canvas.create_text(x, y + radius + 20, text=title, fill=FG_COLOR, font=("Arial", 10))

def draw_limit_dial(canvas, x, y, radius, limit):
    """Рисует левый круг с лимитом"""
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                       outline=OUTLINE_COLOR, width=2, fill=BG_COLOR)

    # Декоративные деления
    for deg in range(0, 360, 22):
        angle_rad = math.radians(deg)
        x_inner = x + (radius - 8) * math.cos(angle_rad)
        y_inner = y + (radius - 8) * math.sin(angle_rad)
        x_outer = x + radius * math.cos(angle_rad)
        y_outer = y + radius * math.sin(angle_rad)
        canvas.create_line(x_inner, y_inner, x_outer, y_outer, fill=TICK_COLOR, width=1)

    # Крупная цифра лимита
    canvas.create_text(x, y, text=f"{limit}", fill=FG_COLOR, font=("Arial", 32, "bold"))
    canvas.create_text(x, y + radius - 20, text="km/h limit", fill=FG_COLOR, font=("Arial", 9))

def read_serial(port, status_label):
    """Чтение данных из последовательного порта в отдельном потоке"""
    global current_speed, speed_limit, serial_connected
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        serial_connected = True
        status_label.config(text=f"Подключено: {port}", fg="green")
        print(f"Успешно подключено к {port}")
        
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("SPEED:"):
                parts = line.split()
                speed_part = parts[0].split(":")[1]
                limit_part = parts[1].split(":")[1]
                current_speed = float(speed_part)
                speed_limit = int(limit_part)
    except Exception as e:
        serial_connected = False
        status_label.config(text=f"Ошибка: {e}", fg="red")
        print(f"Ошибка подключения: {e}")

def update_gui(root, canvas, status_label):
    """Обновление графического интерфейса"""
    canvas.delete("all")
    
    # Статус подключения
    if serial_connected:
        status_label.config(text="Подключено", fg="green")
    else:
        status_label.config(text="Нет подключения", fg="red")
    
    # Левый круг (лимит)
    left_x = WIDTH // 4
    left_y = HEIGHT // 2
    left_radius = 80
    draw_limit_dial(canvas, left_x, left_y, left_radius, speed_limit)
    
    # Центральный спидометр
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    center_radius = 110
    draw_dial(canvas, center_x, center_y, center_radius, current_speed, MAX_SPEED,
              "km/h", tick_step=20, red_threshold=100)
    
    # Правый тахометр
    right_x = 3 * WIDTH // 4
    right_y = HEIGHT // 2
    right_radius = 80
    rpm = current_speed * 40
    if rpm > MAX_RPM:
        rpm = MAX_RPM
    draw_dial(canvas, right_x, right_y, right_radius, rpm, MAX_RPM,
              "x1000 rpm", tick_step=2000)
    
    root.after(50, update_gui, root, canvas, status_label)

def main():
    root = tk.Tk()
    root.title("Speed Limiter System - Arduino")
    root.geometry(f"{WIDTH}x{HEIGHT}")
    root.configure(bg=BG_COLOR)
    
    # Статус-бар
    status_label = tk.Label(root, text="Поиск Arduino...", font=("Arial", 10), 
                            bg=BG_COLOR, fg="blue")
    status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT-30, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()
    
    # Автоматический поиск порта
    port = find_arduino_port()
    if port:
        threading.Thread(target=read_serial, args=(port, status_label), daemon=True).start()
    else:
        status_label.config(text="Arduino не найден! Проверьте подключение.", fg="red")
    
    update_gui(root, canvas, status_label)
    root.mainloop()

if __name__ == "__main__":
    main()