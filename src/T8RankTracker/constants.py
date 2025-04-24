fighter_list = [
        'KAZUYA',
        'JIN',
        'KING',
        'JUN',
        'PAUL',
        'LAW',
        'JACK', #JACK-8 is hard for tesseract to read
        'LARS',
        'XIAOYU',
        'NINA',
        'LEROY',
        'ASUKA',
        'LILI',
        'BRYAN',
        'HWOARANG',
        'CLAUDIO',
        'AZUCENA',
        'RAVEN',
        'LEO',
        'STEVE',
        'KUMA',
        'YOSHIMITSU',
        'SHAHEEN',
        'DRAGUNOV',
        'FENG',
        'PANDA',
        'LEE',
        'ALISA',
        'ZAFINA',
        'DEVILJIN', #spaces are removed in tesseract post-processing
        'VICTOR',
        'REINA'
    ]

#for logging print statements
class asciiColor:
    reset = '\033[0m'

    #background
    class bg:
        BLACK = '\033[40m'
        RED = '\033[41m'
        GREEN = '\033[42m'
        YELLOW = '\033[43m'
        BLUE = '\033[44m'
        MAGENTA = '\033[45m'
        CYAN = '\033[46m'
        WHITE = '\033[47m'

        class bright:
            BLACK = '\033[100m'
            RED = '\033[101m'
            GREEN = '\033[102m'
            YELLOW = '\033[103m'
            BLUE = '\033[104m'
            MAGENTA = '\033[105m'
            CYAN = '\033[106m'
            WHITE = '\033[107m'

    #foreground
    class fg:
        BLACK = '\033[30m'
        RED = '\033[31m'
        GREEN = '\033[32m'
        YELLOW = '\033[33m'
        BLUE = '\033[34m'
        MAGENTA = '\033[35m'
        CYAN = '\033[36m'
        WHITE = '\033[37m'

        class bright:
            BLACK = '\033[90m'
            RED = '\033[91m'
            GREEN = '\033[92m'
            YELLOW = '\033[93m'
            BLUE = '\033[94m'
            MAGENTA = '\033[95m'
            CYAN = '\033[96m'
            WHITE = '\033[97m'

    class style:
        bold = '\033[1m'
        italic = '\033[3m'
        underline = '\033[4m'
        strike = '\033[9m'