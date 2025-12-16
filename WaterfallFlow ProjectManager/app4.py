import wx
import wx.dataview
import time
import threading
import json
import os

# -------------------------------------------------------------------------
# OFFLINE TEMPLATE LOGIC
# -------------------------------------------------------------------------

TEMPLATES = {
    "software": {
        "name": "Enterprise Software Project",
        "description": "Full Waterfall SDLC with Validation & Verification.",
        "phases": [
            ("Requirements", "Gathering needs", [
                ("Stakeholder Interviews", 5, "Alice (PM)", [("Prep", 1), ("Interview", 3), ("Review", 1)]),
                ("Spec Doc", 7, "Alice (PM)", [])
            ]),
            ("Design", "System architecture", [
                ("UI Mockups", 5, "Carol (Design)", [("Wireframes", 2), ("Hi-Fi", 3)]),
                ("DB Schema", 3, "Dave (DBA)", [])
            ]),
            ("Implementation", "Coding", [
                ("Backend Setup", 5, "Backend Team", []),
                ("API Dev", 10, "Backend Team", []),
                ("Frontend", 10, "Frontend Team", [])
            ]),
            ("Verification", "Internal Testing", [
                ("Code Reviews", 3, "Tech Lead", []),
                ("Unit Testing", 5, "Dev Team", []),
                ("Integration Testing", 5, "QA", [])
            ]),
            ("Validation", "Requirements Check", [
                ("User Acceptance Testing (UAT)", 5, "Stakeholders", []),
                ("Compliance Check", 2, "Legal", [])
            ]),
            ("Final Test & Demo", "Final steps", [
                ("Performance Test", 3, "QA", []),
                ("Final Client Demo", 1, "PM & Lead", []),
                ("Sign-off Meeting", 1, "Sponsors", [])
            ]),
            ("Maintenance", "Support", [
                ("Production Deployment", 1, "DevOps", []),
                ("User Training", 2, "Alice (PM)", [])
            ])
        ]
    },
    "construction": {
        "name": "Construction Project",
        "description": "Physical infrastructure project.",
        "phases": [
            ("Planning", "Permits and blueprints", [
                ("Site Survey", 3, "Surveyor", []),
                ("Permits", 14, "Manager", [])
            ]),
            ("Foundation", "Ground work", [
                ("Excavation", 5, "Crew A", []),
                ("Pouring Concrete", 7, "Crew A", [])
            ]),
            ("Structure", "Framing", [
                ("Framing", 10, "Carpenters", [("Walls", 6), ("Roof", 4)])
            ])
        ]
    },
    "generic": {
        "name": "General Project",
        "description": "Generic 5-stage waterfall plan.",
        "phases": [
            ("Initiation", "Define goals", [("Kickoff Meeting", 1, "Lead", [])]),
            ("Planning", "Roadmap", [("Resource Plan", 3, "Manager", [])]),
            ("Execution", "Core work", [
                ("Task A", 5, "Team A", [("Subtask 1", 2), ("Subtask 2", 3)]),
                ("Task B", 5, "Team B", [])
            ]),
            ("Monitoring", "Quality check", [("Review", 2, "Lead", [])]),
            ("Closing", "Handover", [("Final Report", 1, "Admin", [])])
        ]
    }
}


def generate_offline_plan(prompt):
    prompt = prompt.lower()
    if any(x in prompt for x in ['soft', 'app', 'web', 'code', 'program']):
        key = 'software'
    elif any(x in prompt for x in ['build', 'house', 'construct', 'civil']):
        key = 'construction'
    else:
        key = 'generic'

    data = TEMPLATES[key]

    project_data = {
        "name": data["name"],
        "description": f"{data['description']}",
        "phases": []
    }

    for p_name, p_desc, tasks in data["phases"]:
        phase_tasks = []
        for t in tasks:
            title, duration, assignee, sub_raw = t
            subtasks_list = []
            sub_duration_sum = 0
            for st in sub_raw:
                subtasks_list.append({"title": st[0], "durationDays": st[1]})
                sub_duration_sum += st[1]

            final_duration = sub_duration_sum if subtasks_list else duration
            phase_tasks.append({
                "title": title,
                "durationDays": final_duration,
                "assignee": assignee,
                "subtasks": subtasks_list
            })

        phase_obj = {
            "name": p_name,
            "description": p_desc,
            "tasks": phase_tasks
        }
        project_data["phases"].append(phase_obj)

    return project_data


# -------------------------------------------------------------------------
# DATA MODELS
# -------------------------------------------------------------------------
class Subtask:
    def __init__(self, title, duration, completed=False):
        self.title = title
        self.duration = duration
        self.completed = completed

    def to_dict(self):
        return {
            "title": self.title,
            "durationDays": self.duration,
            "completed": self.completed
        }


class Task:
    def __init__(self, title, duration, assignee="Unassigned", completed=False):
        self.title = title
        self.duration = duration
        self.assignee = assignee
        self.completed = completed
        self.subtasks = []

    def to_dict(self):
        return {
            "title": self.title,
            "durationDays": self.duration,
            "assignee": self.assignee,
            "completed": self.completed,
            "subtasks": [s.to_dict() for s in self.subtasks]
        }


class Phase:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.tasks = []

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks]
        }


class Project:
    def __init__(self, name="New Project", description=""):
        self.name = name
        self.description = description
        self.phases = []

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "phases": [p.to_dict() for p in self.phases]
        }


# -------------------------------------------------------------------------
# WORKER
# -------------------------------------------------------------------------
class OfflineWorker(threading.Thread):
    def __init__(self, prompt, callback):
        threading.Thread.__init__(self)
        self.prompt = prompt
        self.callback = callback

    def run(self):
        time.sleep(0.5)
        try:
            data = generate_offline_plan(self.prompt)
            self.callback(data, None)
        except Exception as e:
            self.callback(None, str(e))


# -------------------------------------------------------------------------
# MAIN FRAME - DARK THEME
# -------------------------------------------------------------------------
class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='WaterfallFlow (Dark Edition)', size=(1280, 850))

        # -- Theme Colors (Dracula/Dark Inspired) --
        self.col_bg_main = wx.Colour(30, 30, 30)  # Deep grey background
        self.col_bg_panel = wx.Colour(45, 45, 48)  # Lighter grey for panels
        self.col_fg_text = wx.Colour(220, 220, 220)  # Off-white text
        self.col_accent = wx.Colour(64, 169, 255)  # Blue accent
        self.col_danger = wx.Colour(255, 85, 85)  # Red for delete
        self.col_input_bg = wx.Colour(60, 60, 60)  # Input fields

        self.project = None
        self.current_phase = None
        self.row_map = {}

        self.init_ui()
        self.Center()

    def init_ui(self):
        self.SetBackgroundColour(self.col_bg_main)

        # -- Menus --
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, '&New Project', 'Start fresh')
        file_menu.Append(wx.ID_OPEN, '&Open Project...	Ctrl+O', 'Open JSON file')
        file_menu.Append(wx.ID_SAVE, '&Save Project...	Ctrl+S', 'Save to JSON')
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, 'E&xit', 'Quit')
        menubar.Append(file_menu, '&File')

        tools_menu = wx.Menu()
        tools_menu.Append(wx.ID_ANY, '&Wizard...', 'Generate plan')
        menubar.Append(tools_menu, '&Tools')
        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, lambda e: self.Close(), id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_new_project, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_save_project, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_open_project, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_generate, id=wx.ID_ANY)

        # -- Splitter --
        self.splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE | wx.SP_NOBORDER)
        self.splitter.SetBackgroundColour(self.col_bg_main)

        # --- LEFT PANEL: Tree ---
        self.tree_panel = wx.Panel(self.splitter)
        self.tree_panel.SetBackgroundColour(self.col_bg_panel)

        tree_sizer = wx.BoxSizer(wx.VERTICAL)
        lbl_tree = wx.StaticText(self.tree_panel, label=" PROJECT PHASES")
        lbl_tree.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl_tree.SetForegroundColour(wx.Colour(150, 150, 150))

        self.tree = wx.TreeCtrl(self.tree_panel,
                                style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_ROW_LINES | wx.BORDER_NONE)
        self.tree.SetBackgroundColour(self.col_bg_panel)
        self.tree.SetForegroundColour(self.col_fg_text)

        self.root = self.tree.AddRoot("Root")
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_phase_selected, self.tree)

        tree_sizer.Add(lbl_tree, 0, wx.ALL, 15)
        tree_sizer.Add(self.tree, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.tree_panel.SetSizer(tree_sizer)

        # --- RIGHT PANEL: Content ---
        self.right_panel = wx.Panel(self.splitter)
        self.right_panel.SetBackgroundColour(self.col_bg_main)
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header Area
        self.header_panel = wx.Panel(self.right_panel)
        self.header_panel.SetBackgroundColour(self.col_bg_main)
        header_sizer = wx.BoxSizer(wx.VERTICAL)

        self.lbl_phase_name = wx.StaticText(self.header_panel, label="Loading...")
        self.lbl_phase_name.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.lbl_phase_name.SetForegroundColour(self.col_accent)

        self.lbl_phase_desc = wx.StaticText(self.header_panel, label="...")
        self.lbl_phase_desc.SetForegroundColour(wx.Colour(180, 180, 180))

        header_sizer.Add(self.lbl_phase_name, 0, wx.BOTTOM, 5)
        header_sizer.Add(self.lbl_phase_desc, 0, wx.EXPAND)
        self.header_panel.SetSizer(header_sizer)

        # Task List (DataViewListCtrl)
        self.task_list = wx.dataview.DataViewListCtrl(self.right_panel, style=wx.BORDER_NONE)
        self.task_list.SetBackgroundColour(wx.Colour(40, 40, 40))
        self.task_list.SetForegroundColour(self.col_fg_text)

        # Add Columns
        col_done = self.task_list.AppendToggleColumn("✔", width=40)
        col_task = self.task_list.AppendTextColumn("Task / Subtask (Double-click to edit)", width=450)
        col_dur = self.task_list.AppendTextColumn("Duration", width=80)
        col_assign = self.task_list.AppendTextColumn("Assignee", width=150)

        self.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.on_list_selection, self.task_list)
        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_list_double_click, self.task_list)

        # -- Controls Panel (Bottom) --
        self.controls_panel = wx.Panel(self.right_panel)
        self.controls_panel.SetBackgroundColour(wx.Colour(50, 50, 50))
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)

        def make_lbl(label):
            t = wx.StaticText(self.controls_panel, label=label)
            t.SetForegroundColour(self.col_fg_text)
            return t

        # Title Input
        self.txt_title = wx.TextCtrl(self.controls_panel, value="", size=(200, -1), style=wx.BORDER_SIMPLE)
        self.txt_title.SetBackgroundColour(self.col_input_bg)
        self.txt_title.SetForegroundColour(self.col_fg_text)
        self.txt_title.SetHint("Task Title")

        # Duration Input
        self.spin_dur = wx.SpinCtrl(self.controls_panel, value="1", min=1, max=365, size=(60, -1),
                                    style=wx.BORDER_SIMPLE)
        self.spin_dur.SetBackgroundColour(self.col_input_bg)
        self.spin_dur.SetForegroundColour(self.col_fg_text)

        # Assignee Input
        self.txt_assignee = wx.TextCtrl(self.controls_panel, value="", size=(120, -1), style=wx.BORDER_SIMPLE)
        self.txt_assignee.SetBackgroundColour(self.col_input_bg)
        self.txt_assignee.SetForegroundColour(self.col_fg_text)
        self.txt_assignee.SetHint("Assignee")

        # Buttons
        self.btn_add_task = wx.Button(self.controls_panel, label="+ Task")
        self.btn_add_task.SetBackgroundColour(self.col_accent)
        self.btn_add_task.SetForegroundColour(wx.WHITE)

        self.btn_add_sub = wx.Button(self.controls_panel, label="+ Subtask")
        self.btn_add_sub.Disable()

        self.btn_delete = wx.Button(self.controls_panel, label="Delete")
        self.btn_delete.SetBackgroundColour(self.col_danger)
        self.btn_delete.SetForegroundColour(wx.WHITE)
        self.btn_delete.Disable()

        self.Bind(wx.EVT_BUTTON, self.on_add_task, self.btn_add_task)
        self.Bind(wx.EVT_BUTTON, self.on_add_subtask, self.btn_add_sub)
        self.Bind(wx.EVT_BUTTON, self.on_delete_item, self.btn_delete)

        # Layout Controls
        controls_sizer.Add(make_lbl("Title:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)
        controls_sizer.Add(self.txt_title, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        controls_sizer.Add(make_lbl("Days:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        controls_sizer.Add(self.spin_dur, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        controls_sizer.Add(make_lbl("Who:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        controls_sizer.Add(self.txt_assignee, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        controls_sizer.Add(self.btn_add_task, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)
        controls_sizer.Add(self.btn_add_sub, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)

        # Spacer
        controls_sizer.AddStretchSpacer(1)
        controls_sizer.Add(self.btn_delete, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 15)

        self.controls_panel.SetSizer(controls_sizer)

        # Assemble Right Panel
        self.right_sizer.Add(self.header_panel, 0, wx.EXPAND | wx.ALL, 25)
        # Separator line
        line = wx.StaticLine(self.right_panel)
        line.SetBackgroundColour(wx.Colour(60, 60, 60))
        self.right_sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 25)

        self.right_sizer.Add(self.task_list, 1, wx.EXPAND | wx.ALL, 25)
        self.right_sizer.Add(self.controls_panel, 0, wx.EXPAND | wx.ALL, 0)
        self.right_panel.SetSizer(self.right_sizer)

        # Splitter Settings
        self.splitter.SplitVertically(self.tree_panel, self.right_panel, 280)
        self.splitter.SetMinimumPaneSize(200)

        self.CreateStatusBar()
        self.SetStatusText("Ready")

        # Load DEFAULT "Software" Project on startup
        self.create_default_project()

    def create_default_project(self):
        # Instead of empty, load the Software template
        data = generate_offline_plan("Software Development")
        self.load_project_data(data, None)

    def on_new_project(self, event):
        self.project = Project("Untitled Project", "Start by adding phases or using the Wizard.")
        self.refresh_tree()
        self.lbl_phase_name.SetLabel("New Project")
        self.lbl_phase_desc.SetLabel("Empty project created.")
        self.task_list.DeleteAllItems()
        self.row_map = {}

    def on_save_project(self, event):
        if not self.project: return

        with wx.FileDialog(self, "Save Project", wildcard="JSON files (*.json)|*.json",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'w') as file:
                    json.dump(self.project.to_dict(), file, indent=4)
                self.SetStatusText(f"Saved to {pathname}")
                wx.MessageBox(f"Project saved successfully!", "Saved", wx.OK | wx.ICON_INFORMATION)
            except IOError:
                wx.LogError("Cannot save current data in file '%s'." % pathname)

    def on_open_project(self, event):
        with wx.FileDialog(self, "Open Project", wildcard="JSON files (*.json)|*.json",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            try:
                with open(pathname, 'r') as file:
                    data = json.load(file)
                    self.load_project_data(data, None)
                    self.SetStatusText(f"Loaded {pathname}")
            except IOError:
                wx.LogError("Cannot open file '%s'." % pathname)

    def on_generate(self, event):
        dlg = wx.TextEntryDialog(self, 'Project Type:', 'Project Wizard')
        if dlg.ShowModal() == wx.ID_OK:
            prompt = dlg.GetValue()
            if prompt:
                self.SetStatusText("Generating...")
                worker = OfflineWorker(prompt, self.on_wizard_complete)
                worker.start()
        dlg.Destroy()

    def on_wizard_complete(self, data, error):
        wx.CallAfter(self.load_project_data, data, error)

    def load_project_data(self, data, error):
        if error:
            wx.MessageBox(f"Error: {error}", "Error", wx.ICON_ERROR)
            return
        self.project = Project(data.get('name'), data.get('description'))
        self.SetTitle(f"{self.project.name} - WaterfallFlow (Dark Mode)")

        for p_data in data.get('phases', []):
            phase = Phase(p_data.get('name'), p_data.get('description'))
            for t_data in p_data.get('tasks', []):
                # Handle both 'durationDays' (from template/save) and legacy 'duration' if any
                dur = t_data.get('durationDays') if t_data.get('durationDays') is not None else t_data.get('duration',
                                                                                                           1)
                t = Task(t_data.get('title'), dur, t_data.get('assignee', 'Unassigned'), t_data.get('completed', False))

                for st_data in t_data.get('subtasks', []):
                    sdur = st_data.get('durationDays') if st_data.get('durationDays') is not None else st_data.get(
                        'duration', 1)
                    st = Subtask(st_data.get('title'), sdur, st_data.get('completed', False))
                    t.subtasks.append(st)
                phase.tasks.append(t)
            self.project.phases.append(phase)

        self.refresh_tree()
        self.SetStatusText("Plan generated.")

        # Select first phase automatically
        if self.project.phases:
            first_item = self.tree.GetFirstChild(self.root)[0]
            if first_item.IsOk():
                self.tree.SelectItem(first_item)

    def refresh_tree(self):
        self.tree.DeleteAllItems()
        self.root = self.tree.AddRoot("Project")
        for phase in self.project.phases:
            self.tree.AppendItem(self.root, phase.name, data=phase)
        self.tree.ExpandAll()

    def on_phase_selected(self, event):
        item = event.GetItem()
        if not item.IsOk(): return
        data = self.tree.GetItemData(item)
        self.task_list.DeleteAllItems()
        self.row_map = {}

        if isinstance(data, Phase):
            self.current_phase = data
            self.lbl_phase_name.SetLabel(data.name)
            self.lbl_phase_desc.SetLabel(data.description)
            self.refresh_task_list()
        else:
            self.current_phase = None
            if self.project:
                self.lbl_phase_name.SetLabel(self.project.name)
                self.lbl_phase_desc.SetLabel(self.project.description)
            else:
                self.lbl_phase_name.SetLabel("No Project")
                self.lbl_phase_desc.SetLabel("")

    def refresh_task_list(self):
        if not self.current_phase: return
        self.task_list.DeleteAllItems()
        self.row_map = {}
        idx = 0

        for task in self.current_phase.tasks:
            self.task_list.AppendItem([task.completed, task.title, str(task.duration), task.assignee])
            self.row_map[idx] = {'type': 'task', 'obj': task}
            idx += 1

            for st in task.subtasks:
                self.task_list.AppendItem([st.completed, f"    ↳ {st.title}", str(st.duration), ""])
                self.row_map[idx] = {'type': 'subtask', 'obj': st, 'parent': task}
                idx += 1

    def on_list_selection(self, event):
        row = self.task_list.GetSelectedRow()
        has_sel = (row != wx.NOT_FOUND and row in self.row_map)

        self.btn_delete.Enable(has_sel)

        if has_sel:
            item = self.row_map[row]
            if item['type'] == 'task':
                self.btn_add_sub.Enable()
                self.btn_add_sub.SetLabel(f"+ Sub")
            else:
                self.btn_add_sub.Disable()
                self.btn_add_sub.SetLabel("+ Sub")
        else:
            self.btn_add_sub.Disable()
            self.btn_add_sub.SetLabel("+ Subtask")

    def on_list_double_click(self, event):
        row = self.task_list.GetSelectedRow()
        if row == wx.NOT_FOUND or row not in self.row_map: return

        item = self.row_map[row]
        obj = item['obj']

        dlg = wx.TextEntryDialog(self, 'Rename:', 'Edit', obj.title)
        if dlg.ShowModal() == wx.ID_OK:
            new_title = dlg.GetValue()
            if new_title:
                obj.title = new_title
                if item['type'] == 'task':
                    self.task_list.SetValue(new_title, row, 1)
                else:
                    self.task_list.SetValue(f"    ↳ {new_title}", row, 1)
        dlg.Destroy()

    def on_add_task(self, event):
        if not self.current_phase:
            wx.MessageBox("Select a Phase on the left.", "No Phase Selected")
            return

        title = self.txt_title.GetValue()
        if not title: return

        t = Task(title, self.spin_dur.GetValue(), self.txt_assignee.GetValue())
        self.current_phase.tasks.append(t)

        self.txt_title.SetValue("")
        self.spin_dur.SetValue(1)
        self.txt_assignee.SetValue("")

        self.refresh_task_list()

    def on_add_subtask(self, event):
        row = self.task_list.GetSelectedRow()
        if row == wx.NOT_FOUND or row not in self.row_map: return

        item = self.row_map[row]
        if item['type'] != 'task': return

        title = self.txt_title.GetValue()
        if not title: return

        parent_task = item['obj']
        st = Subtask(title, self.spin_dur.GetValue())
        parent_task.subtasks.append(st)

        self.txt_title.SetValue("")
        self.spin_dur.SetValue(1)
        self.refresh_task_list()

    def on_delete_item(self, event):
        row = self.task_list.GetSelectedRow()
        if row == wx.NOT_FOUND or row not in self.row_map: return

        item = self.row_map[row]

        if wx.MessageBox("Are you sure you want to delete this item?", "Confirm Delete",
                         wx.YES_NO | wx.ICON_QUESTION) != wx.YES:
            return

        if item['type'] == 'task':
            task = item['obj']
            if task in self.current_phase.tasks:
                self.current_phase.tasks.remove(task)
        elif item['type'] == 'subtask':
            st = item['obj']
            parent = item['parent']
            if st in parent.subtasks:
                parent.subtasks.remove(st)

        self.refresh_task_list()


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
