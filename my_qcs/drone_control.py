import tkinter as tk

connected = False
armed = False
airborne = False
current_mode = None
current_altitude = 0.0

VALID_CONNECTION_STRINGS = {"127.0.0.1:14550"}

MODE_NAMES = ["GUIDED", "LOITER", "STABILIZE", "LAND", "RTL"]

WINDOW_BG = "#171322"
SECTION_BG = "#241B35"
INPUT_BG = "#130F20"
TEXT_COLOR = "#F7F0FF"
SECONDARY_COLOR = "#D0C2E8"
BUTTON_BG = "#8052CC"
BUTTON_ACTIVE_BG = "#9B6BE8"
DISABLED_COLOR = "#776B89"
SUCCESS_COLOR = "#A7E8C3"
ERROR_COLOR = "#FF8FA3"


def log(message):
    print(f"[SIMULATION] {message}", flush=True)


def set_status(message, error=False):
    status_label.config(
        text=message,
        fg=ERROR_COLOR if error else SUCCESS_COLOR
    )


def connect():
    global connected, current_mode
    connection_str = connection_entry.get().strip()
    if not connection_str:
        set_status("Enter a connection string.", True)
        log("Connection string is empty.")
        return
    if connection_str not in VALID_CONNECTION_STRINGS:
        set_status("Invalid connection string.", True)
        log(f"Invalid connection string '{connection_str}'.")
        return

    if connected:
        log("Already connected.")
        return

    connected = True
    current_mode = "STABILIZE"

    log(f"Simulated connection accepted: {connection_str}")
    log(f"Initial flight mode: {current_mode}")

    set_status("Connected (simulation).")
    update_controls()


def disconnect():
    global connected, current_mode
    if not connected:
        log("Already disconnected.")
        return
    if armed:
        set_status("Disarm before disconnecting.", True)
        log("Disarm before disconnecting.")
        return
    connected = False
    current_mode = None
    log("Simulation connection closed.")
    set_status("Disconnected.")
    update_controls()


def set_mode(mode):
    global current_mode
    if not connected:
        set_status("Connect first.", True)
        log(f"Cannot select {mode}; not connected.")
        return
    if mode not in MODE_NAMES:
        log(f"Unknown mode '{mode}'.")
        return
    if mode == "LAND":
        land()
        return
    if mode == "RTL":
        rtl()
        return
    current_mode = mode
    log(f"Flight mode changed to {mode}.")
    set_status(f"Mode selected: {mode} (simulation).")
    update_controls()


def toggle_arm():
    global armed
    if not connected:
        set_status("Connect first.", True)
        log("Cannot arm; not connected.")
        return
    if not armed:
        if current_mode == "RTL":
            set_status("Cannot arm in RTL mode.", True)
            log("Impossible to arm in RTL mode.")
            return
        if current_mode == "LAND":
            set_status("Cannot arm in LAND mode.", True)
            log("Cannot arm in LAND mode.")
            return
        armed = True
        log(f"Vehicle armed. Mode: {current_mode}.")
        set_status("Vehicle armed (simulation).")
    else:
        if airborne:
            set_status("Land before disarming.", True)
            log("Land before disarming.")
            return
        armed = False
        log("Vehicle disarmed.")
        set_status("Vehicle disarmed (simulation).")
    update_controls()


def takeoff():
    global airborne, current_altitude
    if not connected:
        set_status("Connect first.", True)
        log("Takeoff requires a connection.")
        return
    if not armed:
        set_status("Arm the vehicle first.", True)
        log("Arm before takeoff.")
        return
    if current_mode != "GUIDED":
        set_status("Select GUIDED mode first.", True)
        log("Takeoff requires GUIDED mode.")
        return
    if airborne:
        set_status("Vehicle is already airborne.", True)
        log("Vehicle is already airborne.")
        return
    try:
        altitude = float(altitude_entry.get())
    except ValueError:
        set_status("Enter a valid altitude.", True)
        log("Altitude must be a number.")
        return
    if not 1 <= altitude <= 20:
        set_status("Altitude must be between 1 and 20 meters.", True)
        log("Altitude must be between 1 and 20 m.")
        return
    airborne = True
    current_altitude = altitude
    log(f"Takeoff successful (simulation): {altitude:g} m.")
    set_status(f"Takeoff completed: {altitude:g} m (simulation).")
    update_controls()


def land():
    global current_mode, airborne, current_altitude, armed
    if not connected:
        set_status("Connect first.", True)
        log("LAND requires a connection.")
        return
    if not armed:
        set_status("Arm the vehicle first.", True)
        log("LAND requires an armed vehicle.")
        return
    current_mode = "LAND"
    log("LAND mode selected.")
    airborne = False
    current_altitude = 0.0
    armed = False
    log("Simulated landing complete. Vehicle disarmed.")
    set_status("Landing complete (simulation).")
    update_controls()


def rtl():
    global current_mode, airborne, current_altitude, armed
    if not connected:
        set_status("Connect first.", True)
        log("RTL requires a connection.")
        return
    if not armed:
        set_status("Arm the vehicle first.", True)
        log("RTL requires an armed vehicle.")
        return
    current_mode = "RTL"
    log("RTL mode selected.")
    if airborne:
        airborne = False
        current_altitude = 0.0
        armed = False
        log("Simulated return and landing complete.")
        set_status("Return and landing complete (simulation).")
    else:
        log("RTL selected while on the ground (simulation).")
        set_status("RTL selected (simulation).")
    update_controls()


def update_controls():
    connection_entry.config(
        state="disabled" if connected else "normal"
    )
    connect_button.config(
        state="disabled" if connected else "normal"
    )
    close_button.config(
        state="normal" if connected else "disabled"
    )
    mode_state = "normal" if connected else "disabled"
    for button in mode_buttons:
        button.config(state=mode_state)
    arm_button.config(
        state=mode_state,
        text="Disarm" if armed else "Arm"
    )
    takeoff_allowed = (
        connected
        and armed
        and current_mode == "GUIDED"
        and not airborne
    )
    takeoff_button.config(
        state="normal" if takeoff_allowed else "disabled"
    )
    mode_label.config(
        text=f"Flight mode: {current_mode or 'None'}"
    )
    connection_status_label.config(
        text=f"Connection: {'Connected (Simulation)' if connected else 'Disconnected'}"
    )
    arming_status_label.config(
        text=f"Arming: {'Armed' if armed else 'Disarmed'}"
    )
    flight_status_label.config(
        text=f"Flight status: {'Airborne' if airborne else 'On ground'}"
    )
    altitude_label.config(
        text=f"Altitude: {current_altitude:g} m"
    )


root = tk.Tk()
root.title("Ground Control Station")
root.geometry("650x570")
root.minsize(600, 540)
root.configure(bg=WINDOW_BG)

default_font = ("Arial", 10)
heading_font = ("Arial", 11, "bold")

root.option_add("*Font", default_font)
root.option_add("*LabelFrame*Label.font", heading_font)
root.option_add("*Button.Cursor", "hand2")

connection_frame = tk.LabelFrame(
    root,
    text="Connection",
    padx=12,
    pady=10,
    bg=SECTION_BG,
    fg=TEXT_COLOR,
    font=heading_font,
    bd=1,
    relief="groove"
)
connection_frame.pack(fill="x", padx=16, pady=(14, 8))

tk.Label(
    connection_frame,
    text="Connection string:",
    bg=SECTION_BG,
    fg=TEXT_COLOR
).grid(row=0, column=0, padx=6, pady=7, sticky="w")

connection_entry = tk.Entry(
    connection_frame,
    width=27,
    bg=INPUT_BG,
    fg=TEXT_COLOR,
    insertbackground=TEXT_COLOR,
    relief="flat",
    highlightthickness=1,
    highlightbackground="#A879F5",
    highlightcolor=BUTTON_BG
)
connection_entry.grid(row=0, column=1, padx=6, pady=7, sticky="ew")

connect_button = tk.Button(
    connection_frame,
    text="Connect",
    command=connect,
    bg=BUTTON_BG,
    fg=TEXT_COLOR,
    activebackground=BUTTON_ACTIVE_BG,
    activeforeground=TEXT_COLOR,
    disabledforeground=DISABLED_COLOR,
    relief="flat",
    padx=14,
    pady=5
)
connect_button.grid(row=0, column=2, padx=6, pady=7)

close_button = tk.Button(
    connection_frame,
    text="Close Connection",
    command=disconnect,
    state="disabled",
    bg="#49365F",
    fg=TEXT_COLOR,
    activebackground="#60477B",
    activeforeground=TEXT_COLOR,
    disabledforeground=DISABLED_COLOR,
    relief="flat",
    padx=10,
    pady=5
)
close_button.grid(row=1, column=2, padx=6, pady=7)

connection_frame.columnconfigure(1, weight=1)

mode_frame = tk.LabelFrame(
    root,
    text="Flight Modes",
    padx=10,
    pady=12,
    bg=SECTION_BG,
    fg=TEXT_COLOR,
    font=heading_font,
    bd=1,
    relief="groove"
)
mode_frame.pack(fill="x", padx=16, pady=8)

mode_buttons = []

for col, mode in enumerate(MODE_NAMES):
    button = tk.Button(
        mode_frame,
        text=mode,
        width=10,
        command=lambda selected_mode=mode: set_mode(selected_mode),
        state="disabled",
        bg=BUTTON_BG,
        fg=TEXT_COLOR,
        activebackground=BUTTON_ACTIVE_BG,
        activeforeground=TEXT_COLOR,
        disabledforeground=DISABLED_COLOR,
        relief="flat",
        pady=7
    )
    button.grid(row=0, column=col, padx=4, pady=5, sticky="ew")
    mode_buttons.append(button)
    mode_frame.columnconfigure(col, weight=1)

takeoff_frame = tk.LabelFrame(
    root,
    text="Takeoff",
    padx=12,
    pady=10,
    bg=SECTION_BG,
    fg=TEXT_COLOR,
    font=heading_font,
    bd=1,
    relief="groove"
)
takeoff_frame.pack(fill="x", padx=16, pady=8)

tk.Label(
    takeoff_frame,
    text="Altitude (meters):",
    bg=SECTION_BG,
    fg=TEXT_COLOR
).grid(row=0, column=0, padx=6, pady=7, sticky="w")

altitude_entry = tk.Entry(
    takeoff_frame,
    width=10,
    bg=INPUT_BG,
    fg=TEXT_COLOR,
    insertbackground=TEXT_COLOR,
    relief="flat",
    highlightthickness=1,
    highlightbackground="#58456F",
    highlightcolor=BUTTON_BG
)
altitude_entry.grid(row=0, column=1, padx=6, pady=7, sticky="w")
altitude_entry.insert(0, "10")

takeoff_button = tk.Button(
    takeoff_frame,
    text="Takeoff",
    command=takeoff,
    state="disabled",
    bg=BUTTON_BG,
    fg=TEXT_COLOR,
    activebackground=BUTTON_ACTIVE_BG,
    activeforeground=TEXT_COLOR,
    disabledforeground=DISABLED_COLOR,
    relief="flat",
    padx=22,
    pady=6
)
takeoff_button.grid(row=0, column=2, padx=12, pady=7)

takeoff_frame.columnconfigure(1, weight=1)

arm_frame = tk.Frame(root, bg=WINDOW_BG)
arm_frame.pack(fill="x", padx=16, pady=8)

arm_button = tk.Button(
    arm_frame,
    text="Arm",
    width=18,
    command=toggle_arm,
    state="disabled",
    bg="#7040A8",
    fg=TEXT_COLOR,
    activebackground="#8754C2",
    activeforeground=TEXT_COLOR,
    disabledforeground=DISABLED_COLOR,
    relief="flat",
    pady=8
)
arm_button.pack()

status_frame = tk.LabelFrame(
    root,
    text="Vehicle Status",
    padx=12,
    pady=10,
    bg=SECTION_BG,
    fg=TEXT_COLOR,
    font=heading_font,
    bd=1,
    relief="groove"
)
status_frame.pack(fill="x", padx=16, pady=8)

connection_status_label = tk.Label(
    status_frame,
    text="Connection: Disconnected",
    anchor="w",
    bg=SECTION_BG,
    fg=SECONDARY_COLOR
)
connection_status_label.pack(fill="x", pady=2)

arming_status_label = tk.Label(
    status_frame,
    text="Arming: Disarmed",
    anchor="w",
    bg=SECTION_BG,
    fg=SECONDARY_COLOR
)
arming_status_label.pack(fill="x", pady=2)

mode_label = tk.Label(
    status_frame,
    text="Flight mode: None",
    anchor="w",
    bg=SECTION_BG,
    fg=SECONDARY_COLOR
)
mode_label.pack(fill="x", pady=2)

flight_status_label = tk.Label(
    status_frame,
    text="Flight status: On ground",
    anchor="w",
    bg=SECTION_BG,
    fg=SECONDARY_COLOR
)
flight_status_label.pack(fill="x", pady=2)

altitude_label = tk.Label(
    status_frame,
    text="Altitude: 0 m",
    anchor="w",
    bg=SECTION_BG,
    fg=SECONDARY_COLOR
)
altitude_label.pack(fill="x", pady=2)

status_label = tk.Label(
    root,
    text="Status: Disconnected",
    wraplength=600,
    justify="center",
    bg=WINDOW_BG,
    fg=SECONDARY_COLOR,
    padx=10,
    pady=5
)
status_label.pack(fill="x", padx=16, pady=(2, 10))

log("Application started in simulation mode.")
update_controls()
root.mainloop()
