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
        self.col_bg_main = wx.Colour(30, 30, 30)
        self.col_bg_panel = wx.Colour(45, 45, 48)
        self.col_fg_text = wx.Colour(220, 220, 220)
        self.col_accent = wx.Colour(64, 169, 255)
        self.col_danger = wx.Colour(255, 85, 85)
        self.col_input_bg = wx.Colour(60, 60, 60)

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
        file_menu.Append(wx.ID_NEW, '&New Project\tCtrl+N', 'Start fresh')
        file_menu.Append(wx.ID_OPEN, '&Open Project...\tCtrl+O', 'Open JSON file')
        file_menu.Append(wx.ID_SAVE, '&Save Project...\tCtrl+S', 'Save to JSON')
        file_menu.AppendSeparator()
        file_menu.Append(wx.ID_EXIT, 'E&xit', 'Quit')
        menubar.Append(file_menu, '&File')

        tools_menu = wx.Menu()
        # Create a unique ID for the Wizard menu item
        self.wizard_id = wx.NewId()
        tools_menu.Append(self.wizard_id, '&Wizard...\tCtrl+W', 'Generate plan from description')
        menubar.Append(tools_menu, '&Tools')
        self.SetMenuBar(menubar)

        # Bind each menu item to its specific handler with the correct ID
        self.Bind(wx.EVT_MENU, self.on_exit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_new_project, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.on_save_project, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.on_open_project, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.on_generate, id=self.wizard_id)  # Use the specific ID

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

        # Columns
        self.task_list.AppendToggleColumn("✔", width=40, mode=wx.dataview.DATAVIEW_CELL_ACTIVATABLE)
        self.task_list.AppendTextColumn("Task / Subtask (Double-click to edit)", width=450)
        self.task_list.AppendTextColumn("Duration", width=80)
        self.task_list.AppendTextColumn("Assignee", width=150)

        self.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.on_list_selection, self.task_list)
        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_list_double_click, self.task_list)
        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self.on_item_value_changed, self.task_list)

        # -- Controls Panel (Bottom) --
        self.controls_panel = wx.Panel(self.right_panel)
        self.controls_panel.SetBackgroundColour(wx.Colour(50, 50, 50))
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)

        def make_lbl(label):
            t = wx.StaticText(self.controls_panel, label=label)
            t.SetForegroundColour(self.col_fg_text)
            return t

        self.txt_title = wx.TextCtrl(self.controls_panel, value="", size=(200, -1), style=wx.BORDER_SIMPLE)
        self.txt_title.SetBackgroundColour(self.col_input_bg)
        self.txt_title.SetForegroundColour(self.col_fg_text)
        self.txt_title.SetHint("Task Title")

        self.spin_dur = wx.SpinCtrl(self.controls_panel, value="1", min=1, max=365, size=(60, -1),
                                    style=wx.BORDER_SIMPLE)
        self.spin_dur.SetBackgroundColour(self.col_input_bg)
        self.spin_dur.SetForegroundColour(self.col_fg_text)

        self.txt_assignee = wx.TextCtrl(self.controls_panel, value="", size=(120, -1), style=wx.BORDER_SIMPLE)
        self.txt_assignee.SetBackgroundColour(self.col_input_bg)
        self.txt_assignee.SetForegroundColour(self.col_fg_text)
        self.txt_assignee.SetHint("Assignee")

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

        controls_sizer.Add(make_lbl("Title:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)
        controls_sizer.Add(self.txt_title, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        controls_sizer.Add(make_lbl("Days:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        controls_sizer.Add(self.spin_dur, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        controls_sizer.Add(make_lbl("Who:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        controls_sizer.Add(self.txt_assignee, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        controls_sizer.Add(self.btn_add_task, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)
        controls_sizer.Add(self.btn_add_sub, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        controls_sizer.AddStretchSpacer(1)
        controls_sizer.Add(self.btn_delete, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 15)

        self.controls_panel.SetSizer(controls_sizer)

        self.right_sizer.Add(self.header_panel, 0, wx.EXPAND | wx.ALL, 25)
        line = wx.StaticLine(self.right_panel)
        line.SetBackgroundColour(wx.Colour(60, 60, 60))
        self.right_sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 25)
        self.right_sizer.Add(self.task_list, 1, wx.EXPAND | wx.ALL, 25)
        self.right_sizer.Add(self.controls_panel, 0, wx.EXPAND | wx.ALL, 0)
        self.right_panel.SetSizer(self.right_sizer)

        self.splitter.SplitVertically(self.tree_panel, self.right_panel, 280)
        self.splitter.SetMinimumPaneSize(200)

        self.CreateStatusBar()
        self.SetStatusText("Ready")

        # Load default project
        self.create_default_project()

    def create_default_project(self):
        data = generate_offline_plan("Software Development")
        self.load_project_data(data, None)

    def on_exit(self, event):
        self.Close()

    def on_new_project(self, event):
        self.project = Project("Untitled Project", "Start by adding phases or using the Wizard.")
        self.refresh_tree()
        self.lbl_phase_name.SetLabel("New Project")
        self.lbl_phase_desc.SetLabel("Empty project created.")
        self.task_list.DeleteAllItems()
        self.row_map = {}
        self.SetStatusText("New project created.")

    def on_save_project(self, event):
        if not self.project:
            wx.MessageBox("No active project to save.", "Nothing to Save", wx.OK | wx.ICON_WARNING)
            return

        # Create a proper file save dialog
        dlg = wx.FileDialog(
            self,
            message="Save project file",
            defaultDir=os.getcwd(),
            defaultFile="myproject.json",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )

        if dlg.ShowModal() == wx.ID_OK:
            # Get the file path
            pathname = dlg.GetPath()

            # Ensure .json extension
            if not pathname.lower().endswith('.json'):
                pathname += '.json'

            try:
                # Save the project as JSON
                with open(pathname, 'w', encoding='utf-8') as f:
                    json.dump(self.project.to_dict(), f, indent=2, ensure_ascii=False)

                wx.MessageBox(f"Project saved successfully to:\n{pathname}",
                              "Save Successful", wx.OK | wx.ICON_INFORMATION)
                self.SetStatusText(f"Saved: {os.path.basename(pathname)}")

            except Exception as e:
                wx.MessageBox(f"Error saving file:\n{str(e)}",
                              "Save Error", wx.OK | wx.ICON_ERROR)

        dlg.Destroy()

    def on_open_project(self, event):
        # Create a proper file open dialog
        dlg = wx.FileDialog(
            self,
            message="Open project file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="JSON files (*.json)|*.json|All files (*.*)|*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )

        if dlg.ShowModal() == wx.ID_OK:
            # Get the file path
            pathname = dlg.GetPath()

            try:
                # Load the JSON file
                with open(pathname, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Load the project data
                self.load_project_data(data, None)

                wx.MessageBox(f"Project loaded successfully:\n{os.path.basename(pathname)}",
                              "Load Successful", wx.OK | wx.ICON_INFORMATION)
                self.SetStatusText(f"Loaded: {os.path.basename(pathname)}")

            except Exception as e:
                wx.MessageBox(f"Error loading file:\n{str(e)}",
                              "Load Error", wx.OK | wx.ICON_ERROR)

        dlg.Destroy()

    def on_generate(self, event):
        dlg = wx.TextEntryDialog(self, 'Describe your project (e.g., "software app", "house construction"):',
                                 'Project Wizard')
        if dlg.ShowModal() == wx.ID_OK:
            prompt = dlg.GetValue()
            if prompt.strip():
                self.SetStatusText("Generating plan...")
                worker = OfflineWorker(prompt.strip(), self.on_wizard_complete)
                worker.start()
            else:
                wx.MessageBox("Please enter a project description.", "Empty Input", wx.OK | wx.ICON_INFORMATION)
        dlg.Destroy()

    def on_wizard_complete(self, data, error):
        wx.CallAfter(self.load_project_data, data, error)

    def load_project_data(self, data, error):
        if error:
            wx.MessageBox(f"Generation error: {error}", "Error", wx.ICON_ERROR)
            return
        if not data:
            wx.MessageBox("No data received.", "Error", wx.ICON_ERROR)
            return

        self.project = Project(data.get('name', 'Untitled'), data.get('description', ''))
        self.SetTitle(f"{self.project.name} - WaterfallFlow (Dark Mode)")

        for p_data in data.get('phases', []):
            phase = Phase(p_data.get('name'), p_data.get('description'))
            for t_data in p_data.get('tasks', []):
                dur = t_data.get('durationDays', t_data.get('duration', 1))
                t = Task(
                    title=t_data.get('title', 'Untitled Task'),
                    duration=dur,
                    assignee=t_data.get('assignee', 'Unassigned'),
                    completed=t_data.get('completed', False)
                )
                for st_data in t_data.get('subtasks', []):
                    sdur = st_data.get('durationDays', st_data.get('duration', 1))
                    st = Subtask(
                        title=st_data.get('title', 'Untitled Subtask'),
                        duration=sdur,
                        completed=st_data.get('completed', False)
                    )
                    t.subtasks.append(st)
                phase.tasks.append(t)
            self.project.phases.append(phase)

        self.refresh_tree()
        if self.project.phases:
            first_item = self.tree.GetFirstChild(self.root)[0]
            if first_item.IsOk():
                self.tree.SelectItem(first_item)
        else:
            self.lbl_phase_name.SetLabel(self.project.name)
            self.lbl_phase_desc.SetLabel(self.project.description)
            self.task_list.DeleteAllItems()
            self.row_map = {}
        self.SetStatusText("Project loaded.")

    def refresh_tree(self):
        self.tree.DeleteAllItems()
        self.root = self.tree.AddRoot("Project")
        for phase in self.project.phases:
            self.tree.AppendItem(self.root, phase.name, data=phase)
        self.tree.ExpandAll()

    def on_phase_selected(self, event):
        item = event.GetItem()
        if not item.IsOk():
            return
        data = self.tree.GetItemData(item)
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
            self.task_list.DeleteAllItems()
            self.row_map = {}

    def refresh_task_list(self):
        self.task_list.DeleteAllItems()
        self.row_map = {}
        idx = 0
        if not self.current_phase:
            return
        for task in self.current_phase.tasks:
            self.task_list.AppendItem([task.completed, task.title, str(task.duration), task.assignee])
            self.row_map[idx] = {'type': 'task', 'obj': task}
            idx += 1
            for st in task.subtasks:
                self.task_list.AppendItem([st.completed, f"    ↳ {st.title}", str(st.duration), ""])
                self.row_map[idx] = {'type': 'subtask', 'obj': st, 'parent': task}
                idx += 1

    def on_item_value_changed(self, event):
        item = event.GetItem()
        if not item.IsOk():
            return
        row = self.task_list.ItemToRow(item)
        if row == wx.NOT_FOUND or row not in self.row_map:
            return
        is_checked = self.task_list.GetValue(row, 0)
        obj = self.row_map[row]['obj']
        obj.completed = bool(is_checked)

    def on_list_selection(self, event):
        row = self.task_list.GetSelectedRow()
        has_sel = (row != wx.NOT_FOUND and row in self.row_map)
        self.btn_delete.Enable(has_sel)
        if has_sel:
            item_data = self.row_map[row]
            if item_data['type'] == 'task':
                self.btn_add_sub.Enable()
                self.btn_add_sub.SetLabel("+ Sub")
            else:
                self.btn_add_sub.Disable()
        else:
            self.btn_add_sub.Disable()
            self.btn_add_sub.SetLabel("+ Subtask")

    def on_list_double_click(self, event):
        row = self.task_list.GetSelectedRow()
        if row == wx.NOT_FOUND or row not in self.row_map:
            return
        item = self.row_map[row]
        obj = item['obj']
        dlg = wx.TextEntryDialog(self, 'Rename:', 'Edit Item', obj.title)
        if dlg.ShowModal() == wx.ID_OK:
            new_title = dlg.GetValue().strip()
            if new_title:
                obj.title = new_title
                if item['type'] == 'task':
                    self.task_list.SetValue(new_title, row, 1)
                else:
                    self.task_list.SetValue(f"    ↳ {new_title}", row, 1)
        dlg.Destroy()

    def on_add_task(self, event):
        if not self.current_phase:
            wx.MessageBox("Please select a phase from the left panel.", "No Phase Selected", wx.OK | wx.ICON_WARNING)
            return
        title = self.txt_title.GetValue().strip()
        if not title:
            wx.MessageBox("Task title cannot be empty.", "Invalid Input", wx.OK | wx.ICON_WARNING)
            return
        t = Task(title, self.spin_dur.GetValue(), self.txt_assignee.GetValue().strip() or "Unassigned")
        self.current_phase.tasks.append(t)
        self.txt_title.SetValue("")
        self.spin_dur.SetValue(1)
        self.txt_assignee.SetValue("")
        self.refresh_task_list()

    def on_add_subtask(self, event):
        row = self.task_list.GetSelectedRow()
        if row == wx.NOT_FOUND or row not in self.row_map:
            return
        item = self.row_map[row]
        if item['type'] != 'task':
            wx.MessageBox("Please select a main task to add a subtask.", "Invalid Selection", wx.OK | wx.ICON_WARNING)
            return
        title = self.txt_title.GetValue().strip()
        if not title:
            wx.MessageBox("Subtask title cannot be empty.", "Invalid Input", wx.OK | wx.ICON_WARNING)
            return
        parent_task = item['obj']
        st = Subtask(title, self.spin_dur.GetValue())
        parent_task.subtasks.append(st)
        self.txt_title.SetValue("")
        self.spin_dur.SetValue(1)
        self.refresh_task_list()

    def on_delete_item(self, event):
        row = self.task_list.GetSelectedRow()
        if row == wx.NOT_FOUND or row not in self.row_map:
            return
        if wx.MessageBox("Are you sure you want to delete this item?", "Confirm Delete",
                         wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION) != wx.YES:
            return
        item = self.row_map[row]
        if item['type'] == 'task':
            if item['obj'] in self.current_phase.tasks:
                self.current_phase.tasks.remove(item['obj'])
        elif item['type'] == 'subtask':
            parent = item['parent']
            if item['obj'] in parent.subtasks:
                parent.subtasks.remove(item['obj'])
        self.refresh_task_list()


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()