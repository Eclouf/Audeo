import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

class SettingsApp(toga.App):

    def startup(self):
        main_box = toga.Box(style=Pack(direction=COLUMN))

        option_container = toga.OptionContainer(style=Pack(flex=1))

        # option general
        general_options_box = toga.Box()
        
        switches = [
            ('ignore errors', 'Ignore download and postprocessing errors. The download will be considered successful even if the postprocessing fails'),
            ]

        left_column = toga.Box(style=Pack(direction=COLUMN, padding=5))
        right_column = toga.Box(style=Pack(direction=COLUMN, padding=5))

        def on_switch_change(widget):
            print(f'Switch {widget.text} is now {"on" if widget.value else "off"}')
        
        for switch, description in switches:
            switch_widget = toga.Switch(switch, on_change=on_switch_change)
            left_column.add(switch_widget)
            right_column.add(toga.Label(description, style=Pack(padding_left=10)))

        general_options_box.add(toga.Box(children=[left_column, right_column], style=Pack(direction=ROW)))
        general_options = toga.ScrollContainer(content=general_options_box)
        
        # Option network
        network_options_box = toga.Box()
        network_switches = [
            ('proxy URL', 'Use the specified HTTP/HTTPS/SOCKS proxy. To enable SOCKS proxy, specify a proper scheme, e.g. socks5://user:pass@127.0.0.1:1080/. Pass in an empty string (  proxy "") for direct connection'),
            ]

        network_left_column = toga.Box(style=Pack(direction=COLUMN, padding=5))
        network_right_column = toga.Box(style=Pack(direction=COLUMN, padding=5))

        for switch, description in network_switches:
            switch_widget = toga.Switch(switch, on_change=on_switch_change)
            network_left_column.add(switch_widget)
            network_right_column.add(toga.Label(description, style=Pack(padding_left=10)))

        network_options_box.add(toga.Box(children=[network_left_column, network_right_column], style=Pack(direction=ROW)))
        network_options = toga.ScrollContainer(content=network_options_box)
       
        
        # geo restriction
        geo_restriction = toga.Box()
        video_selection = toga.Box()
        download_options = toga.Box()
        filesystem_options = toga.Box()
        thumbnail_options = toga.Box()
        internet_shortcut_options = toga.Box()
        verbosity_simulation_options = toga.Box()
        workarounds = toga.Box()
        authentication_options = toga.Box()
        sponsorBlock_options = toga.Box()
        extractor_options = toga.Box()

        option_container.content.append('General Options', general_options)
        option_container.content.append('Network Options', network_options)
        option_container.content.append('Geo Restriction', geo_restriction)
        option_container.content.append('Video Selection', video_selection)
        option_container.content.append('Download Options', download_options)
        option_container.content.append('Filesystem Options', filesystem_options)
        option_container.content.append('Thumbnail Options', thumbnail_options)
        option_container.content.append('Internet Shortcut Options', internet_shortcut_options)
        option_container.content.append('Verbosity and Simulation Options', verbosity_simulation_options)
        option_container.content.append('Workarounds', workarounds)
        option_container.content.append('Authentication Options', authentication_options)
        option_container.content.append('SponsorBlock Options', sponsorBlock_options)
        option_container.content.append('Extractor Options', extractor_options)

        main_box.add(option_container)

        self.main_window = toga.Window(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

def main():
    return SettingsApp('Settings', 'org.beeware.settingsapp')

if __name__ == '__main__':
    main().main_loop()