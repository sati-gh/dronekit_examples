import tkinter as tk


class AppStyle:
    WINDOW_BG = "#171322"
    SECTION_BG = "#241B35"
    INPUT_BG = "#130F20"

    TEXT_COLOR = "#F7F0FF"
    SECONDARY_COLOR = "#D0C2E8"

    BUTTON_BG = "#8052CC"
    BUTTON_ACTIVE_BG = "#9B6BE8"
    ARM_BUTTON_BG = "#7040A8"

    DISABLED_COLOR = "#776B89"
    SUCCESS_COLOR = "#A7E8C3"
    ERROR_COLOR = "#FF8FA3"

    RC_BAR_COLOR = "#A7E8C3"
    RC_CENTER_COLOR = "#D0C2E8"

    DEFAULT_FONT = ("Arial", 10)
    HEADING_FONT = ("Arial", 11, "bold")

    WINDOW_TITLE = "Ground Control Station"
    WINDOW_SIZE = "1400x800"
    MIN_WIDTH = 1100
    MIN_HEIGHT = 650

    @classmethod
    def configure_window(cls, root):
        root.title(cls.WINDOW_TITLE)
        root.geometry(cls.WINDOW_SIZE)
        root.minsize(cls.MIN_WIDTH, cls.MIN_HEIGHT)
        root.resizable(True, True)
        root.configure(bg=cls.WINDOW_BG)
        root.option_add("*Font", cls.DEFAULT_FONT)
        root.option_add("*Button.Cursor", "hand2")

    @classmethod
    def make_button(cls, parent, text, command, bg=None):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg or cls.BUTTON_BG,
            fg=cls.TEXT_COLOR,
            activebackground=cls.BUTTON_ACTIVE_BG,
            activeforeground=cls.TEXT_COLOR,
            disabledforeground=cls.DISABLED_COLOR,
            relief="flat",
            padx=10,
            pady=5,
        )

    @classmethod
    def make_status_label(cls, parent, text):
        label = tk.Label(
            parent,
            text=text,
            anchor="w",
            bg=cls.SECTION_BG,
            fg=cls.SECONDARY_COLOR,
        )
        label.pack(fill="x", pady=2)
        return label

    @classmethod
    def make_section(cls, parent, title, padx=12, pady=10):
        return tk.LabelFrame(
            parent,
            text=title,
            padx=padx,
            pady=pady,
            bg=cls.SECTION_BG,
            fg=cls.TEXT_COLOR,
            font=cls.HEADING_FONT,
            bd=1,
            relief="groove",
        )

    @classmethod
    def make_label(cls, parent, text):
        return tk.Label(
            parent,
            text=text,
            bg=cls.SECTION_BG,
            fg=cls.TEXT_COLOR,
        )

    @classmethod
    def make_entry(cls, parent, width=None):
        return tk.Entry(
            parent,
            width=width,
            bg=cls.INPUT_BG,
            fg=cls.TEXT_COLOR,
            insertbackground=cls.TEXT_COLOR,
            relief="flat",
        )
        
    @classmethod
    def make_checkbutton(cls, parent, text, variable, command=None):
        return tk.Checkbutton(
            parent, text=text, variable=variable, command=command,
            bg=cls.SECTION_BG, fg=cls.TEXT_COLOR,
            activebackground=cls.SECTION_BG,
            activeforeground=cls.TEXT_COLOR,
            selectcolor=cls.INPUT_BG,
            disabledforeground=cls.DISABLED_COLOR, relief="flat"
        )

    @classmethod
    def make_rc_channel(cls, parent, channel, name, keys, initial_value):
        frame = tk.Frame(parent, bg=cls.SECTION_BG)
        cls.make_label(frame, f"CH{channel} {name}").pack(pady=(0, 2))
        tk.Label(frame, text=keys, bg=cls.SECTION_BG,
                 fg=cls.SECONDARY_COLOR).pack(pady=(0, 4))
        canvas = tk.Canvas(
            frame, width=42, height=110, bg=cls.INPUT_BG,
            highlightthickness=1, highlightbackground=cls.DISABLED_COLOR,
            bd=0
        )
        canvas.pack()
        value_label = cls.make_label(frame, f"{initial_value} us")
        value_label.pack(pady=(4, 0))
        return {"frame": frame, "canvas": canvas,
                "value_label": value_label}


