from nicegui import ui

servers = [
    ['tester1', '127.0.0.1'],
    ['tester2', '127.0.0.1'],
    ['pc1', '127.0.0.1'],
    ['pc2', '127.0.0.1'],
]


with ui.grid(columns=2).style('width: 100%;'):
    for server in servers:
        with ui.card():
            with ui.row().style('width: 100%; display: flex; justify-content: space-between; align-items: center'):
                ui.label(server[0])
                #ui.chip(server[1],icon='warning', color='red')
                ui.chip(server[1],icon='check', color='green')
            with ui.grid(columns=2):
                ui.button('load firmware')
            ui.textarea()
            
ui.run(port=8080)