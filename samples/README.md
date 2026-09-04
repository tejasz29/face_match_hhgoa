# Sample images

Drop the input image you want to run the pipeline on in this folder, e.g.
`samples/input.jpg`, then run:

```bash
python main.py --image samples/input.jpg
```

**What makes a good demo image?** For the reverse-image-search stage to find a
real *social media* post, the photo must already be published online (the search
matches the image, not the person across different photos — see "Known
limitations" in the top-level README). A widely-shared photo of a public figure,
or one of your own already-posted photos, works best.

Image files in this folder are gitignored on purpose — don't commit personal
photos or copyrighted images.

**Ethics:** only run this on images you are authorized to process.
