import undetected_chromedriver as uc
from profiles import Profiles
from nicegui import ui, app
from config import Config
from loguru import logger
from kkutu import Kkutu
from modes import Modes
from midas import Midas

midas = None
driver = None

@ui.refreshable
def renderWordList():
    with ui.list().classes("w-full space-y-2").style('font-family: "Nanum Myeongjo"'):
        ui.item_label('단어').props('header').classes('text-bold p-0')
        if Kkutu.foundWords:
            for word in Kkutu.foundWords:
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

def renderHistoryList():
    with ui.row():
        ui.item_label('이번 턴에 사용한 단어').props('header').classes('text-bold p-0')
        with ui.list().classes("w-full space-y-2").style('font-family: "Nanum Myeongjo"'):
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

def renderDelList():
    with ui.row():
        ui.item_label('삭제할 단어').props('header').classes('text-bold p-0')
        with ui.list().classes("w-full space-y-2").style('font-family: "Nanum Myeongjo"'):
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

async def startUp():
    global driver, midas
    if driver is not None:
        return
    logger.debug("Initializing undetected-chromdriver...")
    options = uc.ChromeOptions()
    options.add_argument('--mute-audio')
    driver = uc.Chrome(options=options, user_data_dir=Profiles.getPath(), use_subprocess=True)
    midas = Midas(driver)
    Kkutu.updateUI = renderWordList.refresh
    midas.start_running()

def cleanUp():
    midas.stop_running()
    driver.quit()

ui.timer(0.1, startUp, once=True)
app.on_shutdown(cleanUp)

ui.add_head_html('<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">')
"""Fonts"""
ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible+Mono:ital,wght@0,200..800;1,200..800&family=Nanum+Myeongjo&display=swap" rel="stylesheet">')
ui.add_head_html('<link href="https://fonts.googleapis.com/css2?family=Nanum+Myeongjo&display=swap" rel="stylesheet">')
ui.query(".nicegui-content").classes("p-0")
ui.query("body").style("background-color: #39383b")
ui.dark_mode().enable()

with ui.splitter(value=18).classes('p-0 w-full h-screen bg-stone-900') as splitter:
    with splitter.before:
        with ui.tabs().props('vertical').classes('w-full') as tabs:
            midasTab = ui.tab(' ', icon="fas fa-chess-knight")
            historyTab = ui.tab('  ', icon="history")
            movie = ui.tab('   ', icon='build')
    with splitter.after:
        with ui.tab_panels(tabs, value=midasTab).props('vertical').classes('w-full h-full bg-neutral-900'):
            with ui.tab_panel(midasTab).classes("items-center"):
                ui.label('MAIN').classes('text-h4 w-full').style('font-family: "Atkinson Hyperlegible Mono"')
                with ui.tabs().bind_value(Config, "MODE").classes("bg-stone-800 w-full rounded-lg").style('font-family: "Atkinson Hyperlegible Mono"') as tabs:
                    ui.tab(Modes.blatant, label='Blatant', icon="fas fa-skull").classes("flex-1")
                    ui.tab(Modes.semiBlatant, label='Semi', icon='fas fa-bolt').classes("flex-1")
                    ui.tab(Modes.legit, label='Legit', icon='fas fa-ghost').classes("flex-1")
                with ui.row().classes("rounded-lg bg-stone-800 w-full items-center justify-between"):
                    ui.label("KILL SWITCH").classes("pl-4").style('font-family: "Atkinson Hyperlegible Mono"')
                    ui.switch().bind_value(Config, "killSwitch").props('color="red-8" keep-color icon="shield" unchecked-icon="close" size="xl"')
                with ui.scroll_area().classes("border-stone-800 bg-stone-800 w-full rounded-lg p-0"):
                    renderWordList()
            with ui.tab_panel(historyTab):
                ui.label('HISTORY').classes('text-h4 w-full').style('font-family: "Atkinson Hyperlegible Mono"')
                renderHistoryList()
                renderDelList()
            with ui.tab_panel(movie):
                ui.label('Movies').classes('text-h4')
                ui.label('Content of movies')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(native=True, title="MidasChair: Standard Edition", window_size=(400, 560), fullscreen=False)
