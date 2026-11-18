from dataclasses import dataclass, field
from .console_auth import ConsoleAuth
from .tabs import Tab

@dataclass
class AppState:
    # tracks current tab and what's visible
    current_tab: Tab = Tab.MESSAGES
    enabled_tabs: set = field(default_factory=lambda: {Tab.MESSAGES, Tab.FILES, Tab.NET})
    console_stage: ConsoleAuth = ConsoleAuth.LOCKED

    def navigate(self, tab: Tab):
        # switch current tab
        self.current_tab = tab

    def is_tab_enabled(self, tab: Tab):
        # check if tab should be shown
        return tab in self.enabled_tabs

    def enable_tab(self, tab: Tab):
        # show this tab
        self.enabled_tabs.add(tab)

    def set_console_stage(self, stage: ConsoleAuth):
        # update auth state
        self.console_stage = stage

    def is_console_authorized(self):
        # check if we got access
        return self.console_stage == ConsoleAuth.AUTHORIZED
