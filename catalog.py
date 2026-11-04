from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class Studio:
    key: str
    name: str
    country: str
    founder: str
    founded: int


@dataclass(frozen=True)
class Game:
    key: str
    title: str
    studio: str
    publisher: str
    year: int
    genres: List[str]
    platforms: List[str]
    sequel_of: str = ""


@dataclass
class GameCatalog:
    studios: List[Studio] = field(default_factory=list)
    games: List[Game] = field(default_factory=list)

    def studio_keys(self):
        return {studio.key for studio in self.studios}

    def publishers(self):
        return sorted({game.publisher for game in self.games})

    def platforms(self):
        return sorted({platform for game in self.games for platform in game.platforms})

    def genres(self):
        return sorted({genre for game in self.games for genre in game.genres})

    def countries(self):
        return sorted({studio.country for studio in self.studios})

    def founders(self):
        return sorted({studio.founder for studio in self.studios})

    def summary(self):
        return {
            "ігор": len(self.games),
            "студій": len(self.studios),
            "видавців": len(self.publishers()),
            "платформ": len(self.platforms()),
            "жанрів": len(self.genres()),
            "країн": len(self.countries()),
            "засновників": len(self.founders()),
        }


STUDIOS = [
    Studio("gsc", "GSC Game World", "Україна", "Сергій Григорович", 1995),
    Studio("4a", "4A Games", "Мальта", "Андрій Прохоров", 2006),
    Studio("cdpr", "CD Projekt Red", "Польща", "Марцін Івінський", 2002),
    Studio("11bit", "11 bit studios", "Польща", "Гжегож Мєховський", 2010),
    Studio("techland", "Techland", "Польща", "Павел Мархевка", 1991),
    Studio("valve", "Valve", "США", "Гейб Ньюелл", 1996),
    Studio("larian", "Larian Studios", "Бельгія", "Свен Вінке", 1996),
]

GAMES = [
    Game("stalker_soc", "S.T.A.L.K.E.R.: Shadow of Chernobyl", "gsc", "THQ", 2007,
         ["Шутер від першої особи", "Survival horror"], ["Windows"]),
    Game("stalker_cs", "S.T.A.L.K.E.R.: Clear Sky", "gsc", "Deep Silver", 2008,
         ["Шутер від першої особи", "Survival horror"], ["Windows"], "stalker_soc"),
    Game("stalker_cop", "S.T.A.L.K.E.R.: Call of Pripyat", "gsc", "GSC World Publishing", 2009,
         ["Шутер від першої особи", "Survival horror"], ["Windows"], "stalker_cs"),
    Game("cossacks", "Cossacks: European Wars", "gsc", "cdv Software Entertainment", 2001,
         ["Стратегія в реальному часі"], ["Windows"]),
    Game("metro_2033", "Metro 2033", "4a", "THQ", 2010,
         ["Шутер від першої особи", "Survival horror"], ["Windows", "Xbox 360"]),
    Game("metro_ll", "Metro: Last Light", "4a", "Deep Silver", 2013,
         ["Шутер від першої особи"], ["Windows", "Xbox 360", "PlayStation 3"], "metro_2033"),
    Game("metro_exodus", "Metro Exodus", "4a", "Deep Silver", 2019,
         ["Шутер від першої особи"], ["Windows", "PlayStation 4", "Xbox One"], "metro_ll"),
    Game("witcher3", "The Witcher 3: Wild Hunt", "cdpr", "CD Projekt", 2015,
         ["Рольова гра", "Пригодницька гра"],
         ["Windows", "PlayStation 4", "Xbox One", "Nintendo Switch"]),
    Game("cyberpunk", "Cyberpunk 2077", "cdpr", "CD Projekt", 2020,
         ["Рольова гра", "Шутер від першої особи"],
         ["Windows", "PlayStation 4", "Xbox One", "PlayStation 5"]),
    Game("this_war", "This War of Mine", "11bit", "11 bit studios", 2014,
         ["Survival horror", "Симулятор виживання"], ["Windows", "PlayStation 4"]),
    Game("frostpunk", "Frostpunk", "11bit", "11 bit studios", 2018,
         ["Містобудівний симулятор", "Симулятор виживання"],
         ["Windows", "PlayStation 4", "Xbox One"]),
    Game("dying_light", "Dying Light", "techland", "Warner Bros. Interactive Entertainment", 2015,
         ["Survival horror", "Пригодницька гра"],
         ["Windows", "PlayStation 4", "Xbox One"]),
    Game("half_life2", "Half-Life 2", "valve", "Valve", 2004,
         ["Шутер від першої особи"], ["Windows", "Xbox 360"]),
    Game("portal2", "Portal 2", "valve", "Valve", 2011,
         ["Головоломка", "Шутер від першої особи"],
         ["Windows", "PlayStation 3", "Xbox 360"]),
    Game("bg3", "Baldur's Gate 3", "larian", "Larian Studios", 2023,
         ["Рольова гра"], ["Windows", "PlayStation 5", "Xbox Series X/S"]),
]


def default_catalog():
    return GameCatalog(studios=list(STUDIOS), games=list(GAMES))
