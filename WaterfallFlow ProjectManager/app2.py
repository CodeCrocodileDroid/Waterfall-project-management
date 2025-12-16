import wx
import wx.dataview
import time
import threading
import json
import random

# -------------------------------------------------------------------------
# OFFLINE TEMPLATE LOGIC
# -------------------------------------------------------------------------

TEMPLATES = {
    "software": {
        "name": "Software Development",
        "description": "Standard Waterfall SDLC.",
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
                ("UAT", 5, "Stakeholders", []),
                ("Compliance Check", 2, "Legal", [])
            ]),
            ("Final Test & Demo", "Final steps", [
                ("Performance Test", 3, "QA", []),
                ("Client Demo", 1, "PM & Lead", []),
                ("Sign-off", 1, "Sponsors", [])
            ]),
            ("Maintenance", "Support", [
                ("Deployment", 1, "DevOps", []),
                ("Training", 2, "Alice (PM)", [])
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
        "description": f"{data['description']} (Based on: '{prompt[:20]}...')",
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
    def __init__(self, title, duration):
        self.title = title
        self.duration = duration
        self.completed = False


class Task:
    def __init__(self, title, duration, assignee="Unassigned"):
        self.title = title
        self.duration = duration
        self.assignee = assignee
        self.completed = False
        self.subtasks = []


class Phase:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.tasks = []


class Project:
    def __init__(self, name="New Project", description=""):
        self.name = name
        self.description = description
        self.phases = []


# -------------------------------------------------------------------------
# WORKER
# -------------------------------------------------------------------------
class OfflineWorker(threading.Thread):
    def __init__(self, prompt, callback):
        threading.Thread.__init__(self)
        self.prompt = prompt
        self.callback = callback

    def run(self):
        time.sleep(1.0)
        try:
            data = generate_offline_plan(self.prompt)
            self.callback(data, None)
        except Exception as e:
            self.callback(None, str(e))


# -------------------------------------------------------------------------
# MAIN FRAME
# -------------------------------------------------------------------------
class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='WaterfallFlow (Offline Edition)', size=(1200, 850))
        self.project = None
        self.current_phase = None
        # Maps row index to an object dict {'type': 'task'|'subtask', 'obj': object, 'parent': parent_task}
        self.row_map = {}

        self.init_ui()
        self.Center()

    def init_ui(self):
        self.SetBackgroundColour(wx.Colour(245, 247, 250))

        # -- Menus --
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, '&New Project', 'Start fresh')
        file_menu.Append(wx.ID_EXIT, 'E&xit', 'Quit')
        menubar.Append(file_menu, '&File')

        tools_menu = wx.Menu()
        tools_menu.Append(wx.ID_ANY, '&Wizard...', 'Generate plan')
        menubar.Append(tools_menu, '&Tools')
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.on_generate, id=wx.ID_ANY)
        self.Bind(wx.EVT_MENU, self.on_new_project, id=wx.ID_NEW)

        # -- Splitter --
        self.splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)

        # LEFT: Tree
        self.tree_panel = wx.Panel(self.splitter)
        tree_sizer = wx.BoxSizer(wx.VERTICAL)
        lbl_tree = wx.StaticText(self.tree_panel, label=" PROJECT PHASES")
        lbl_tree.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        lbl_tree.SetForegroundColour(wx.Colour(100, 116, 139))
        self.tree = wx.TreeCtrl(self.tree_panel,
                                style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT | wx.TR_FULL_ROW_HIGHLIGHT | wx.TR_ROW_LINES)
        self.root = self.tree.AddRoot("Root")
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_phase_selected, self.tree)
        tree_sizer.Add(lbl_tree, 0, wx.ALL, 10)
        tree_sizer.Add(self.tree, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        self.tree_panel.SetSizer(tree_sizer)

        # RIGHT: Content
        self.right_panel = wx.Panel(self.splitter)
        self.right_panel.SetBackgroundColour(wx.WHITE)
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)

        # Header
        self.header_panel = wx.Panel(self.right_panel)
        self.header_panel.SetBackgroundColour(wx.WHITE)
        header_sizer = wx.BoxSizer(wx.VERTICAL)
        self.lbl_phase_name = wx.StaticText(self.header_panel, label="Welcome")
        self.lbl_phase_name.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.lbl_phase_desc = wx.StaticText(self.header_panel, label="Create a new project or use the Wizard.")
        self.lbl_phase_desc.SetForegroundColour(wx.Colour(100, 100, 100))
        header_sizer.Add(self.lbl_phase_name, 0, wx.BOTTOM, 5)
        header_sizer.Add(self.lbl_phase_desc, 0, wx.EXPAND)
        self.header_panel.SetSizer(header_sizer)

        # Task List
        self.task_list = wx.dataview.DataViewListCtrl(self.right_panel)
        self.task_list.AppendToggleColumn("Done", width=50)
        self.task_list.AppendTextColumn("Task / Subtask (Double-click to edit)", width=400)
        self.task_list.AppendTextColumn("Duration", width=80)
        self.task_list.AppendTextColumn("Assignee", width=150)

        self.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.on_list_selection, self.task_list)
        self.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.on_list_double_click, self.task_list)

        # -- Controls Panel (Bottom of Right Panel) --
        self.controls_panel = wx.Panel(self.right_panel)
        self.controls_panel.SetBackgroundColour(wx.Colour(240, 248, 255))
        controls_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Input: Title
        self.txt_title = wx.TextCtrl(self.controls_panel, value="", size=(200, -1))
        self.txt_title.SetHint("Task or Subtask Title")

        # Input: Duration
        self.spin_dur = wx.SpinCtrl(self.controls_panel, value="1", min=1, max=365, size=(60, -1))

        # Input: Assignee
        self.txt_assignee = wx.TextCtrl(self.controls_panel, value="", size=(120, -1))
        self.txt_assignee.SetHint("Assignee")

        # Buttons
        self.btn_add_task = wx.Button(self.controls_panel, label="Add Task")
        self.btn_add_sub = wx.Button(self.controls_panel, label="Add Subtask")
        self.btn_add_sub.Disable()  # Disabled until a task is selected

        self.Bind(wx.EVT_BUTTON, self.on_add_task, self.btn_add_task)
        self.Bind(wx.EVT_BUTTON, self.on_add_subtask, self.btn_add_sub)

        controls_sizer.Add(wx.StaticText(self.controls_panel, label="Title:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT,
                           10)
        controls_sizer.Add(self.txt_title, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        controls_sizer.Add(wx.StaticText(self.controls_panel, label="Days:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        controls_sizer.Add(self.spin_dur, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        controls_sizer.Add(wx.StaticText(self.controls_panel, label="Who:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
        controls_sizer.Add(self.txt_assignee, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        controls_sizer.Add(self.btn_add_task, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)
        controls_sizer.Add(self.btn_add_sub, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)

        self.controls_panel.SetSizer(controls_sizer)

        # Layout Right
        self.right_sizer.Add(self.header_panel, 0, wx.EXPAND | wx.ALL, 20)
        self.right_sizer.Add(wx.StaticLine(self.right_panel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 20)
        self.right_sizer.Add(self.task_list, 1, wx.EXPAND | wx.ALL, 20)
        self.right_sizer.Add(self.controls_panel, 0, wx.EXPAND | wx.ALL, 0)
        self.right_panel.SetSizer(self.right_sizer)

        self.splitter.SplitVertically(self.tree_panel, self.right_panel, 250)
        self.splitter.SetMinimumPaneSize(200)
        self.CreateStatusBar()
        self.SetStatusText("Ready")
        self.create_default_project()

    def create_default_project(self):
        self.project = Project("Untitled Project", "Start by adding phases or using the Wizard.")
        self.refresh_tree()

    def on_new_project(self, event):
        self.create_default_project()
        self.lbl_phase_name.SetLabel("New Project")
        self.lbl_phase_desc.SetLabel("Empty project created.")
        self.task_list.DeleteAllItems()
        self.row_map = {}

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
        self.SetTitle(f"{self.project.name} - WaterfallFlow")

        for p_data in data.get('phases', []):
            phase = Phase(p_data.get('name'), p_data.get('description'))
            for t_data in p_data.get('tasks', []):
                t = Task(t_data.get('title'), t_data.get('durationDays'), t_data.get('assignee', 'Unassigned'))
                for st_data in t_data.get('subtasks', []):
                    t.subtasks.append(Subtask(st_data.get('title'), st_data.get('durationDays')))
                phase.tasks.append(t)
            self.project.phases.append(phase)

        self.refresh_tree()
        self.SetStatusText("Plan generated.")
        self.lbl_phase_name.SetLabel(self.project.name)
        self.lbl_phase_desc.SetLabel(self.project.description)
        self.task_list.DeleteAllItems()

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
            self.lbl_phase_name.SetLabel(self.project.name if self.project else "Project")
            self.lbl_phase_desc.SetLabel(self.project.description if self.project else "")

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
        if row != wx.NOT_FOUND and row in self.row_map:
            item = self.row_map[row]
            if item['type'] == 'task':
                self.btn_add_sub.Enable()
                self.btn_add_sub.SetLabel(f"Add Subtask to '{item['obj'].title[:10]}...'")
            else:
                self.btn_add_sub.Disable()
                self.btn_add_sub.SetLabel("Add Subtask")
        else:
            self.btn_add_sub.Disable()
            self.btn_add_sub.SetLabel("Add Subtask")

    def on_list_double_click(self, event):
        # Allow editing name on double click
        row = self.task_list.GetSelectedRow()
        if row == wx.NOT_FOUND or row not in self.row_map: return

        item = self.row_map[row]
        obj = item['obj']

        # Show dialog to rename
        dlg = wx.TextEntryDialog(self, 'Rename Task:', 'Edit Task', obj.title)
        if dlg.ShowModal() == wx.ID_OK:
            new_title = dlg.GetValue()
            if new_title:
                obj.title = new_title
                # Refresh UI
                if item['type'] == 'task':
                    self.task_list.SetValue(new_title, row, 1)
                else:
                    self.task_list.SetValue(f"    ↳ {new_title}", row, 1)
        dlg.Destroy()

    def on_add_task(self, event):
        if not self.current_phase:
            wx.MessageBox("Please select a Phase first.", "Info")
            return

        title = self.txt_title.GetValue()
        if not title: return

        t = Task(title, self.spin_dur.GetValue(), self.txt_assignee.GetValue())
        self.current_phase.tasks.append(t)

        # Reset Inputs
        self.txt_title.SetValue("")
        self.txt_assignee.SetValue("")
        self.spin_dur.SetValue(1)

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


if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
