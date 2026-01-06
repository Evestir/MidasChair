import undetected_chromedriver as uc
from sharedVariables import shared
from profiles import Profiles
from nicegui import ui, app
from jamo import h2j, j2hcj
from sqlite import sqlite
from config import Config
from loguru import logger
from kkutu import Kkutu
from modes import Modes, Versions, WordSelModes

def addWord():
    w = addWordInput.value.strip()
    if w:
        shared.sqlite.addTuples([(w, isAckSwitch.value)])
    else:
        ui.notify("단어를 먼저 작성해 주세요!")

def typeWord(word):
    if shared.midas:
        shared.midas.chosenWord = word
    elif shared.pegasus:
        shared.pegasus.chosenWord = word
    """Notify"""
    jam = j2hcj(h2j(word[-1]))
    josa = '를'
    if len(jam) > 2:
        josa = '을'
    ui.notify(f"{word}{josa} 입력했습니다.")

@ui.refreshable
def renderWordList():
    with ui.list().classes("w-full space-y-2"):
        ui.item_label('단어').props('header').classes('text-bold p-0')
        if Kkutu.foundWords:
            for word in Kkutu.foundWords:
                with ui.item(on_click=lambda w=word: typeWord(w)).classes("rounded-lg border"):
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
    with ui.row().classes("w-full bg-stone-800 rounded-lg"):
        ui.item_label('이번 턴에 사용한 단어').props('header').classes('text-bold')
        with ui.scroll_area().classes("w-full p-0"):
            with ui.list().classes("w-full space-y-2"):
                if Kkutu.history:
                    for tup in Kkutu.history:
                        with ui.item().classes("rounded-lg border"):
                            with ui.item_section().props('side'):
                                if tup[1]: # Is Ack?
                                    ui.icon("done_all")
                                else:
                                    ui.icon("check")
                            with ui.item_section():
                                ui.item_label(tup[0])
                else:
                    with ui.item().classes("rounded-lg border"):
                        with ui.item_section().props('side'):
                            ui.icon("question_mark")
                        with ui.item_section():
                            ui.item_label("텅! 비었어요 :3")
                            
@ui.refreshable
def renderDelList():
    with ui.row().classes("w-full bg-stone-800 rounded-lg"):
        ui.item_label('삭제할 단어').props('header').classes('text-bold')
        with ui.scroll_area().classes("w-full p-0"):
            with ui.list().classes("w-full space-y-2"):
                if Kkutu.failed:
                    for word in Kkutu.failed:
                        with ui.item().classes("rounded-lg border"):
                            with ui.item_section().props('side'):
                                ui.icon("coronavirus")
                            with ui.item_section():
                                ui.item_label(word)
                else:
                    with ui.item().classes("rounded-lg border"):
                        with ui.item_section().props('side'):
                            ui.icon("thumb_up_off_alt")
                        with ui.item_section():
                            ui.item_label("삭제할 단어가 없어요 :D")

async def startUp():
    if shared.driver is not None:
        return
    logger.debug("Initializing undetected-chromdriver...")
    options = uc.ChromeOptions()
    # options.add_argument('--mute-audio')
    shared.driver = uc.Chrome(options=options, user_data_dir=Profiles.getSecnPath(), use_subprocess=True)
    shared.sqlite = sqlite()
    if Config.VERSION == Versions.Korea:
        from Daemons.pegasus import Pegasus
        shared.pegasus = Pegasus(shared.driver)
        shared.pegasus.start_running()
    elif Config.VERSION == Versions.Io:
        from Daemons.midas import Midas
        shared.midas = Midas(shared.driver)
        shared.midas.start_running()
    Kkutu.updateUI = update

dynamicUIs = [renderWordList, renderDelList, renderHistoryList]
def update():
    for func in dynamicUIs:
        func.refresh()

def cleanUp():
    if shared.midas and shared.midas.is_running:
        shared.midas.stop_running()
    elif shared.pegasus and shared.pegasus.is_running:
        shared.pegasus.stop_running()
    shared.driver.quit()

ui.timer(0.1, startUp, once=True)
app.on_shutdown(cleanUp)

ui.add_head_html('<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">')
"""Fonts"""
ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Orbit&display=swap" rel="stylesheet">')
ui.query(".nicegui-content").classes("p-0")
ui.query("body").style("background-color: #39383b")
ui.dark_mode().enable()
ui.colors(primary='#ff4d6d')

with ui.splitter(value=18).classes('p-0 w-full h-screen bg-stone-900').style('font-family: "Orbit"').props('separator-class="bg-transparent"') as splitter:
    with splitter.before:
        with ui.tabs().props('vertical').classes('w-full') as tabs:
            midasTab = ui.tab(' ', icon="fas fa-chess-knight")
            historyTab = ui.tab('  ', icon="history")
            dataTab = ui.tab('   ', icon="book")
            settingsTab = ui.tab('    ', icon='build')
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
                        ui.label("자동 입력").classes("pl-4")
                        ui.switch().bind_value(Config, "autoType").props('keep-color icon="auto_awesome" unchecked-icon="close" size="xl"')
                with ui.scroll_area().classes("border-stone-800 bg-stone-800 w-full rounded-lg p-0"):
                    renderWordList()
            with ui.tab_panel(historyTab):
                ui.label('HISTORY').classes('text-h4 w-full')
                renderHistoryList()
                renderDelList()
                ui.label("⠀").classes("pb-0")
            with ui.tab_panel(dataTab):
                ui.label('DATABASE MANAGER').classes('text-h4 w-full')
                with ui.column().classes("rounded-lg bg-stone-800 w-full gap-0"):
                    ui.item_label("단어 추가").props('header').classes('text-bold pb-0')
                    addWordInput = ui.input(label='단어', placeholder='', validation={'Input too long': lambda value: len(value) < 50}).classes("p-3 pt-0 w-full")
                    with ui.row().classes("w-full items-center justify-between px-3 pb-3"):
                        isAckSwitch = ui.switch("어인정").classes("-ml-3")
                        ui.button("추가", on_click=addWord).classes("")
            with ui.tab_panel(settingsTab):
                ui.label('SETTINGS').classes('text-h4')
                with ui.row().classes("w-full bg-stone-800 rounded-lg p-3"):
                    ui.item_label('인게임 설정').props('header').classes('text-bold p-0')
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label("단어 선택 방식")
                        ui.toggle({ WordSelModes.longest: "길이", WordSelModes.random: "무작위" }).bind_value(Config, "wordSelMode").classes("p-0")
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label('단어 색인 개수')
                        ui.slider(min=1, max=50, step=1, value=15).props("label").bind_value(Config, "getWordLimit").classes("w-1/2 p-0")
                with ui.row().classes("w-full bg-stone-800 rounded-lg p-3"):
                    ui.item_label('개발자 설정').props('header').classes('text-bold p-0')
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label('슬립 시간')
                        ui.slider(min=0.01, max=0.2, step=0.01, value=0.05).props("label").bind_value(Config, "sleepTime").classes("w-1/2 p-0")

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=True, title="MidasChair: Standard Edition", window_size=(400, 560), fullscreen=False)
