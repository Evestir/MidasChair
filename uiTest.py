import undetected_chromedriver as uc
from profiles import Profiles
from nicegui import ui, app
from sqlite import sqlite
from config import Config
from loguru import logger
from kkutu import Kkutu
from modes import Modes

words = ["가로자기마당전기기계증폭기", "아랍석유수출국기구", "아날로그시뮬레이션", "딱지조립왕동물친구들", "라이트노벨을읽는것도즐겁지만써보면더즐거울지도몰라요", "마그네슘옥시클로라이드시멘트", "자라투스트라는이렇게말했다"]
Sqlite = sqlite()

def addWord():
    w = addWordInput.value.strip()
    if w:
        Sqlite.addTuples([(w, isAckSwitch.value)])
    else:
        ui.notify("단어를 먼저 작성해 주세요!")

@ui.refreshable
def renderWordList():
    with ui.list().classes("w-full space-y-2"):
        ui.item_label('단어').props('header').classes('text-bold p-0')
        if words:
            for word in words:
                with ui.item(on_click=lambda w=word: ui.notify(f"Typed {w}")).classes("rounded-lg border"):
                    with ui.item_section().props('side'):
                        ui.icon('coronavirus')
                    with ui.item_section():
                        ui.item_label(word)
        else:
            with ui.item().classes("rounded-lg border"):
                with ui.item_section().props('side'):
                    ui.icon('error')
                with ui.item_section():
                    ui.item_label("단어를 찾지 못했습니다.")

@ui.refreshable
def renderHistoryList():
    with ui.row().classes("w-full bg-stone-800 rounded-lg p-0"):
        ui.item_label('이번 턴에 사용한 단어').props('header').classes('text-bold')
        with ui.scroll_area().classes("p-0"):
            with ui.list().classes("w-full space-y-2"):
                if Kkutu.history:
                    for tup in Kkutu.history:
                        with ui.item_section().props('side'):
                            if tup[1]: # Is Ack?
                                ui.icon("done_all")
                            else:
                                ui.icon("check")
                        with ui.item_section():
                            ui.item_label(tup[0])
                else:
                    with ui.item_section().props('side'):
                        ui.icon("question_mark")
                    with ui.item_section():
                        ui.item_label("히스토리에 아무것도 없어요 :3")

@ui.refreshable
def renderDelList():
    with ui.row():
        ui.item_label('삭제할 단어').props('header').classes('text-bold p-0')
        with ui.list().classes("w-full space-y-2"):
            if Kkutu.failed:
                for word in Kkutu.failed:
                    with ui.item_section().props('side'):
                        ui.icon("coronavirus")
                    with ui.item_section():
                        ui.item_label(word)
            else:
                with ui.item_section().props('side'):
                    ui.icon("thumb_up_off_alt")
                with ui.item_section():
                    ui.item_label("삭제할 단어가 없어요 :D")

ui.add_head_html('<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">')
"""Fonts"""
ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Orbit&display=swap" rel="stylesheet">')
ui.query(".nicegui-content").classes("p-0")
ui.dark_mode().enable()

with ui.splitter(value=18).classes('p-0 w-full h-screen bg-stone-900').style('font-family: "Orbit"') as splitter:
    with splitter.before:
        with ui.tabs().props('vertical').classes('w-full') as tabs:
            midasTab = ui.tab(' ', icon="fas fa-chess-knight")
            historyTab = ui.tab('  ', icon="history")
            dataTab = ui.tab('   ', icon="book")
            movie = ui.tab('    ', icon='build')
    with splitter.after:
        with ui.tab_panels(tabs, value=midasTab).props('vertical').classes('w-full h-full bg-neutral-900'):
            with ui.tab_panel(midasTab).classes("items-center"):
                ui.label('MAIN').classes('text-h4 w-full')
                with ui.tabs().bind_value(Config, "MODE").classes("bg-stone-800 w-full rounded-lg") as tabs:
                    ui.tab(Modes.blatant, label='Blatant', icon="fas fa-skull").classes("flex-1")
                    ui.tab(Modes.semiBlatant, label='Semi', icon='fas fa-bolt').classes("flex-1")
                    ui.tab(Modes.legit, label='Legit', icon='fas fa-ghost').classes("flex-1")
                with ui.column().classes("rounded-lg bg-stone-800 w-full"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label("KILL SWITCH").classes("pl-4")
                        ui.switch().bind_value(Config, "killSwitch").props('color="red-8" keep-color icon="shield" unchecked-icon="close" size="xl"')
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label('THREAD SLEEP').classes("pl-4 pb-4 -mt-5")
                        ui.slider(min=0.01, max=0.2, step=0.01, value=0.05).props("label").classes("w-1/2 pr-4 pb-4 -mt-4").bind_value(Config, "sleepTime")
                with ui.scroll_area().classes("border-stone-800 bg-stone-800 w-full rounded-lg p-0"):
                    renderWordList()
            with ui.tab_panel(historyTab):
                ui.label('HISTORY').classes('text-h4 w-full')
                renderHistoryList()
                renderDelList()
            with ui.tab_panel(dataTab):
                ui.label('DATABASE MANAGER').classes('text-h4 w-full')
                with ui.column().classes("rounded-lg bg-stone-800 w-full"):
                    ui.item_label("단어 추가").props('header').classes('text-bold')
                    addWordInput = ui.input(label='단어', placeholder='', validation={'Input too long': lambda value: len(value) < 50}).classes("padding")
                    with ui.row():
                        isAckSwitch = ui.switch("어인정")
                        ui.button("추가", on_click=addWord)
            with ui.tab_panel(movie):
                ui.label('Movies').classes('text-h4')
                ui.label('Content of movies')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=True, title="MidasChair: Standard Edition", window_size=(400, 560), fullscreen=False)
