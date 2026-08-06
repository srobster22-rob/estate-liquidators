"""clipper — turn a long talking-head video into short vertical clips.

The pipeline is four independent stages, each usable on its own:

    transcript.load()  ->  segment.candidates()  ->  score.rank()  ->  render.cut()

Only the ends of the pipeline touch the outside world (`sources` shells out to
yt-dlp, `render` shells out to ffmpeg). Everything in the middle is pure Python
over plain dataclasses, which is what makes it testable without a network.
"""

__version__ = "0.1.0"
