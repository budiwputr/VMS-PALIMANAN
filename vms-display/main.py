import sys
import pygame
import config
import api_client
import renderer


def load_fonts():
    # SysFont 'Arial' is available on Windows; fallback to default monospace
    def f(size):
        try:
            return pygame.font.SysFont('Arial', size)
        except Exception:
            return pygame.font.Font(None, size)

    return {
        'header':   f(config.FONT_HEADER),
        'label':    f(config.FONT_LABEL),
        'plate':    f(config.FONT_PLATE),
        'golongan': f(config.FONT_GOLONGAN),
        'axle_lbl': f(config.FONT_AXLE_LBL),
        'axle_val': f(config.FONT_AXLE_VAL),
        'axle_tot': f(config.FONT_AXLE_TOT),
        'tbl_head': f(config.FONT_TBL_HEAD),
        'tbl_val':  f(config.FONT_TBL_VAL),
        'tbl_name': f(config.FONT_TBL_NAME),
        'status':   f(config.FONT_STATUS),
        'wait':     f(config.FONT_WAIT),
    }


def main():
    pygame.init()

    # Use FULLSCREEN for production, RESIZABLE for development.
    # Change pygame.FULLSCREEN → 0 (or pygame.RESIZABLE) during dev.
    flags  = 0  # pygame.FULLSCREEN untuk production
    screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H), flags)
    pygame.display.set_caption('VMS — PALIMANAN')
    pygame.mouse.set_visible(False)

    clock = pygame.time.Clock()
    fonts = load_fonts()

    api_client.start()

    data = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        new_data, _ = api_client.read_state()
        if new_data is not None or data is None:
            data = new_data

        tick = pygame.time.get_ticks()

        if data is not None:
            renderer.draw_vehicle(screen, fonts, data, tick)
        else:
            renderer.draw_waiting(screen, fonts)

        pygame.display.flip()
        clock.tick(config.FPS)


if __name__ == '__main__':
    main()
