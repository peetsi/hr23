import PySimpleGUI as sg

sg.theme("DarkAmber")
layout= [
        [sg.Text("Module Parameters")],
        [sg.Text("tMeas"), sg.InputText()],
        [sg.Text("timer1Tic"), sg.InputText()],
        [sg.OK(), sg.Exit()],
    ]

window = sg.Window("Modul Parameter Eingebe",layout)

while True:
    event, values = window.read()
    print(event, values)
    if event in (sg.WIN_CLOSED, "Exit"):
        break

window.close()
