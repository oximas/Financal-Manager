"""
Customizable Grid Navigation Template
Shows different navigation schemes you can implement
"""
import customtkinter as ctk


class CustomNavigationGrid(ctk.CTk):
    """Grid with customizable navigation"""
    
    def __init__(self, navigation_mode="excel"):
        super().__init__()
        
        self.title(f"Navigation Mode: {navigation_mode}")
        self.geometry("900x500")
        
        # Grid setup
        self.rows = 5
        self.cols = 4
        self.headers = ["Name", "Age", "City", "Score"]
        self.data = [["", "", "", ""] for _ in range(self.rows)]
        self.entries = []
        self.current_row = 0
        self.current_col = 0
        
        # Choose navigation mode
        self.navigation_mode = navigation_mode
        
        self._create_ui()
        self._setup_navigation()
    
    def _create_ui(self):
        """Create UI"""
        # Title showing current mode
        modes = {
            "excel": "Excel: Arrows move cursor, navigate at boundaries",
            "always": "Always Navigate: Arrows always change cells",
            "ctrl": "Ctrl Mode: Ctrl+Arrows navigate, regular arrows move cursor",
            "vim": "Vim: Ctrl+hjkl navigate",
            "no_wrap": "No Wrap: Navigation stops at edges"
        }
        
        title = ctk.CTkLabel(
            self,
            text=modes.get(self.navigation_mode, "Custom Navigation"),
            font=("Arial", 14, "bold")
        )
        title.pack(pady=10)
        
        # Grid frame
        grid_frame = ctk.CTkFrame(self)
        grid_frame.pack(padx=20, pady=20, fill="both", expand=True)
        
        # Headers
        for col in range(self.cols):
            header = ctk.CTkLabel(
                grid_frame,
                text=self.headers[col],
                font=("Arial", 12, "bold"),
                fg_color="#2B2B2B",
                corner_radius=5,
                width=200,
                height=40
            )
            header.grid(row=0, column=col, padx=2, pady=2, sticky="ew")
        
        # Data entries
        for row in range(self.rows):
            row_entries = []
            for col in range(self.cols):
                entry = ctk.CTkEntry(
                    grid_frame,
                    width=200,
                    height=35,
                    font=("Arial", 12)
                )
                entry.grid(row=row + 1, column=col, padx=2, pady=2, sticky="ew")
                entry.insert(0, self.data[row][col])
                entry.bind('<FocusIn>', lambda e, r=row, c=col: self._on_focus(r, c))
                row_entries.append(entry)
            self.entries.append(row_entries)
        
        for col in range(self.cols):
            grid_frame.grid_columnconfigure(col, weight=1)
        
        self.bind('<Escape>', lambda e: self.quit())
    
    def _setup_navigation(self):
        """Setup navigation based on mode"""
        
        if self.navigation_mode == "excel":
            self._setup_excel_navigation()
        
        elif self.navigation_mode == "always":
            self._setup_always_navigate()
        
        elif self.navigation_mode == "ctrl":
            self._setup_ctrl_navigation()
        
        elif self.navigation_mode == "vim":
            self._setup_vim_navigation()
        
        elif self.navigation_mode == "no_wrap":
            self._setup_no_wrap_navigation()
    
    # ============= NAVIGATION MODE 1: EXCEL ============= #
    
    def _setup_excel_navigation(self):
        """Excel-style: Navigate at text boundaries"""
        for row in range(self.rows):
            for col in range(self.cols):
                entry = self.entries[row][col]
                
                # Up/Down always navigate
                entry.bind('<Up>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, -1, 0, wrap=True))
                entry.bind('<Down>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 1, 0, wrap=True))
                
                # Left/Right navigate at boundaries
                entry.bind('<Left>', lambda e, r=row, c=col: 
                          self._navigate_left(r, c, e, wrap=True))
                entry.bind('<Right>', lambda e, r=row, c=col: 
                          self._navigate_right(r, c, e, wrap=True))
                
                # Enter/Tab
                entry.bind('<Return>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 1, 0, wrap=True))
                entry.bind('<Tab>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, 1, wrap=True))
                entry.bind('<Shift-Tab>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, -1, wrap=True))
    
    # ============= NAVIGATION MODE 2: ALWAYS NAVIGATE ============= #
    
    def _setup_always_navigate(self):
        """All arrows immediately navigate between cells"""
        for row in range(self.rows):
            for col in range(self.cols):
                entry = self.entries[row][col]
                
                # ALL arrows navigate
                entry.bind('<Up>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, -1, 0, wrap=True))
                entry.bind('<Down>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 1, 0, wrap=True))
                entry.bind('<Left>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, -1, wrap=True))
                entry.bind('<Right>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, 1, wrap=True))
                
                entry.bind('<Return>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 1, 0, wrap=True))
                entry.bind('<Tab>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, 1, wrap=True))
    
    # ============= NAVIGATION MODE 3: CTRL+ARROWS ============= #
    
    def _setup_ctrl_navigation(self):
        """Ctrl+Arrows navigate, regular arrows move cursor"""
        for row in range(self.rows):
            for col in range(self.cols):
                entry = self.entries[row][col]
                
                # Ctrl+Arrows navigate
                entry.bind('<Control-Up>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, -1, 0, wrap=True))
                entry.bind('<Control-Down>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 1, 0, wrap=True))
                entry.bind('<Control-Left>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, -1, wrap=True))
                entry.bind('<Control-Right>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, 1, wrap=True))
                
                # Regular arrows do nothing (default cursor behavior)
                
                # Enter/Tab still navigate
                entry.bind('<Return>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 1, 0, wrap=True))
                entry.bind('<Tab>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, 1, wrap=True))
    
    # ============= NAVIGATION MODE 4: VIM ============= #
    
    def _setup_vim_navigation(self):
        """Vim-style hjkl navigation"""
        for row in range(self.rows):
            for col in range(self.cols):
                entry = self.entries[row][col]
                
                # Ctrl+hjkl for navigation
                entry.bind('<Control-h>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, -1, wrap=True))  # left
                entry.bind('<Control-j>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 1, 0, wrap=True))   # down
                entry.bind('<Control-k>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, -1, 0, wrap=True))  # up
                entry.bind('<Control-l>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, 1, wrap=True))   # right
                
                # Regular arrows at boundaries
                entry.bind('<Left>', lambda e, r=row, c=col: 
                          self._navigate_left(r, c, e, wrap=True))
                entry.bind('<Right>', lambda e, r=row, c=col: 
                          self._navigate_right(r, c, e, wrap=True))
                entry.bind('<Up>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, -1, 0, wrap=True))
                entry.bind('<Down>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 1, 0, wrap=True))
    
    # ============= NAVIGATION MODE 5: NO WRAP ============= #
    
    def _setup_no_wrap_navigation(self):
        """Navigation stops at edges (no wrapping)"""
        for row in range(self.rows):
            for col in range(self.cols):
                entry = self.entries[row][col]
                
                # All navigation with wrap=False
                entry.bind('<Up>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, -1, 0, wrap=False))
                entry.bind('<Down>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 1, 0, wrap=False))
                entry.bind('<Left>', lambda e, r=row, c=col: 
                          self._navigate_left(r, c, e, wrap=False))
                entry.bind('<Right>', lambda e, r=row, c=col: 
                          self._navigate_right(r, c, e, wrap=False))
                
                entry.bind('<Return>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 1, 0, wrap=False))
                entry.bind('<Tab>', lambda e, r=row, c=col: 
                          self._navigate_from(r, c, 0, 1, wrap=False))
    
    # ============= CORE NAVIGATION FUNCTIONS ============= #
    
    def _on_focus(self, row: int, col: int):
        """Highlight focused cell"""
        self.current_row = row
        self.current_col = col
        
        for r in range(self.rows):
            for c in range(self.cols):
                if r == row and c == col:
                    self.entries[r][c].configure(border_color="#00FF00", border_width=2)
                else:
                    self.entries[r][c].configure(border_color="#565B5E", border_width=1)
    
    def _navigate_from(self, from_row: int, from_col: int, 
                      row_delta: int, col_delta: int, wrap: bool = True):
        """
        Navigate from a cell
        
        Args:
            from_row: Current row
            from_col: Current column
            row_delta: Row change (-1 up, +1 down)
            col_delta: Col change (-1 left, +1 right)
            wrap: Whether to wrap around edges
        """
        new_row = from_row + row_delta
        new_col = from_col + col_delta
        
        if wrap:
            # Wrap around
            if new_row < 0:
                new_row = self.rows - 1
            elif new_row >= self.rows:
                new_row = 0
            
            if new_col < 0:
                new_col = self.cols - 1
            elif new_col >= self.cols:
                new_col = 0
        else:
            # Stop at edges
            new_row = max(0, min(new_row, self.rows - 1))
            new_col = max(0, min(new_col, self.cols - 1))
        
        # Focus new cell
        self.entries[new_row][new_col].focus_set()
        
        # Smart cursor positioning
        if col_delta > 0:  # Moving right
            self.entries[new_row][new_col].icursor(0)
        elif col_delta < 0:  # Moving left
            self.entries[new_row][new_col].icursor('end')
        else:  # Up/down
            self.entries[new_row][new_col].icursor('end')
        
        return "break"
    
    def _navigate_left(self, row: int, col: int, event, wrap: bool = True):
        """Navigate left only at start of text"""
        entry = self.entries[row][col]
        
        try:
            cursor_pos = entry.index('insert')
            
            if cursor_pos == 0:
                # At start, navigate to previous cell
                return self._navigate_from(row, col, 0, -1, wrap=wrap)
            else:
                # In middle, move cursor
                return None
        except:
            return None
    
    def _navigate_right(self, row: int, col: int, event, wrap: bool = True):
        """Navigate right only at end of text"""
        entry = self.entries[row][col]
        
        try:
            cursor_pos = entry.index('insert')
            text_length = len(entry.get())
            
            if cursor_pos == text_length:
                # At end, navigate to next cell
                return self._navigate_from(row, col, 0, 1, wrap=wrap)
            else:
                # In middle, move cursor
                return None
        except:
            return None


def main():
    """Run with different navigation modes"""
    print("Available navigation modes:")
    print("1. excel - Excel-style (default)")
    print("2. always - Always navigate")
    print("3. ctrl - Ctrl+Arrows navigate")
    print("4. vim - Vim hjkl keys")
    print("5. no_wrap - Stop at edges")
    
    ctk.set_appearance_mode("dark")
    
    # Change this to test different modes
    mode = "vim"  # Try: "always", "ctrl", "vim", "no_wrap"
    
    app = CustomNavigationGrid(navigation_mode=mode)
    app.mainloop()


if __name__ == "__main__":
    main()