# asciinema

To create screencast, i.e., recordings of terminal sessions
that can be replayed later, [asciinema](https://asciinema.org/)
is a very useful tool.

## How to use it?

To start a recording, you type the following.

```bash
$ asciinema rec my_screen.cast
```

Here, `my_screen.cast` is the file name of the recording.

Everything you type, i.e., everything that is shown on standard
output or standard error is recorded.  Note that no keystrokes
are captured, so if you type a password and it is not shown as
output, it will not be part of the recording, making this safe(r)
for demos.

Applications such as editors (`vim`, `emacs`, ...) will be recorded
as well.  However, note that fancy status lines in `vim` may royally
mess up the recording.

Once you are done, you can type exit of crtl-D to quit asciinema and
end the recording.

You can play the recording as follows.

```bash
$ asciinema play my_screen.cast
```

Since a recording is a text file, you can edit it, for instance correcting
typos, or removing some output.  However, note that time stamps for each
output action are absolute with respect to the start of the recording,
removing a part will result in a period of inactivity.  To my knowledge
there is no editing tool, although it would be possible to create one
for simple operations.

It is also possible to upload a cast to https://asciinema.org/, and
make it available via the web.  The website provides a "player" that
show your recording like a movie, but you *can* copy/paste the text
from the recording.  This is a killer featuree ofasciinema in my
opinion.

```bash
$ asciinema upload my_screen.cast
```

Note that you need both an account and an access token for this to work.


## What is it?

1. `hello_world.cast`: recording of editing a C file using `namo`,
   building it with `gcc` and running the appliation.
   [![asciicast](https://asciinema.org/a/597641.svg)](https://asciinema.org/a/597641)
