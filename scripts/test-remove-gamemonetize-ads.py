#!/usr/bin/env python3
"""Regression tests for the GameMonetize HTML cleanup."""
import importlib.util
from pathlib import Path

path = Path(__file__).with_name("remove-gamemonetize-ads.py")
spec = importlib.util.spec_from_file_location("remove_gamemonetize_ads", path)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

fixtures = [
    (
        '<head><script>window.SDK_OPTIONS={gameId:"abc",onEvent:function(a){'
        'if(a.name==="SDK_GAME_START") gmonetize_resume();}};'
        '(function(){var s=document.createElement("script");'
        's.src="https://cdn.jsdelivr.net/gh/st39/sdk@main/sdk.js";'
        's.id="gamemonetize-sdk";document.head.appendChild(s);})();</script>'
        '<script src="game.js"></script></head>',
        '<head><script src="game.js"></script></head>',
    ),
    (
        '<body><script>(function(a,b,c){var d=a.getElementsByTagName(b)[0];'
        'a.getElementById(c)||((a=a.createElement(b)),a.id=c,'
        'a.src="patch/js/gm-sdk-preload.js?v=123",'
        'd.parentNode.insertBefore(a,d))})(document,"script",'
        '"gamemonetize-preload-api");</script><canvas></canvas></body>',
        '<body><canvas></canvas></body>',
    ),
    (
        '<script id="gamemonetize-sdk" src="https://api.gamemonetize.com/sdk.js"></script>'
        '<script>function startGame(){runGame();}</script>',
        '<script>function startGame(){runGame();}</script>',
    ),
    (
        '<script>gmonetize_pause(); gmonetize_resume(); bootGame();</script>',
        '<script>  bootGame();</script>',
    ),
    (
        '<script src="https://example.com/my-game-sdk.js"></script>'
        '<iframe src="https://example.com/game"></iframe>'
        '<canvas id="game"></canvas>',
        '<script src="https://example.com/my-game-sdk.js"></script>'
        '<iframe src="https://example.com/game"></iframe>'
        '<canvas id="game"></canvas>',
    ),
    (
        '<!-- <script src="https://cdn.jsdelivr.net/gh/st39/sdk@main/sdk.js"></script> -->'
        '<p>Game still works.</p>',
        '<p>Game still works.</p>',
    ),
    (
        '<link rel="preload" href="https://example.com/game.css">'
        '<img src="https://example.com/thumbnail.png">'
        '<script>initializeGame();</script>',
        '<link rel="preload" href="https://example.com/game.css">'
        '<img src="https://example.com/thumbnail.png">'
        '<script>initializeGame();</script>',
    ),
]

for index, (before, expected) in enumerate(fixtures, 1):
    after, _ = module.remove_gamemonetize(before)
    assert after == expected, f"fixture {index} was not handled safely:\n{after!r}"
    assert not module.is_monetization_block(after), f"fixture {index} still includes SDK markers"

print(f"GameMonetize cleanup tests passed: {len(fixtures)} fixtures.")
