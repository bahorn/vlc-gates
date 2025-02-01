# VLC Logic Gates

Have you ever wanted to evaluate boolean circuits with VLC?
No?
Well now you can.

Just run `run.sh` and it will start VLC (setup for MacOS).
This uses VLCs HTTP server and the VOD VLM feature (soon to be removed rip) to
concat files to emulate lookup tables (which implement the gates).

The circuit is defined in `main()` in `gen.py`, which is currently just
`NOT (AND 1 1)`.

Circuit evaluation this way is slooow, each step takes at least 0.25 seconds
because I need to add a delay or VLC adds a longer delay itself.

## License

MIT
