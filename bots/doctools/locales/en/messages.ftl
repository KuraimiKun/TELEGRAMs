dt-help =
    📚 <b>Student Document Tools</b>
    Send PDFs, images, DOCX files or assignment text. Your ordered file basket lasts 10 minutes; choose an action below it.
    PDF tools: merge, split, extract, compress, rotate, images, page numbers, watermarks, password lock/unlock.
    Image tools: images to A4 PDF, scan enhancement and OCR to text/Word. Study tools: word/page counts, summaries and ten shareable quiz polls.
    /tools — reopen your basket · /clear — remove it
    /cite DOI, ISBN or URL — APA, MLA, Harvard and Chicago
    /count — reply to a file or text (also works in groups)
    Files are processed in temporary storage and deleted after each job. File references and pasted text expire from the basket after 10 minutes; queued references expire within 6 hours. Only job totals are kept. AI actions send document content to the configured AI provider.
    Share citations from any chat using @{ $bot } cite DOI (enable inline mode in BotFather).
dt-basket =
    📂 <b>Your basket · { $count } files</b>
    { $files }
    Send more files in the desired order, or choose an action. The basket expires 10 minutes after the first file.
dt-empty = Your basket is empty or expired. Send a PDF, image, DOCX or text to begin.
dt-clear = 🗑 Clear basket
dt-cleared = Basket cleared. Jobs already queued will finish.
dt-owner-only = This basket belongs to another user.
dt-queued = ⏳ Job queued. The document worker will send the result here.
dt-processing = Processing your documents…
dt-completed = ✅ Your documents are ready.
dt-count =
    📝 <b>Assignment count</b>
    Words: { $words }
    Characters (including spaces): { $chars }
    Pages: { $pages }
dt-count-help = Reply to text or a PDF/image/DOCX with /count, or use /count your assignment text.
dt-summary = 📖 Summary
dt-cite-help = Send /cite followed by a DOI, ISBN or public URL.
dt-cite-title = 📖 <b>{ $title }</b>
dt-cite-error = I couldn't retrieve citation metadata. Check the DOI, ISBN or public URL and try again.
dt-action-merge = 📎 Merge PDFs
dt-action-split = ✂️ Split PDF
dt-action-extract = 📄 Extract pages
dt-action-compress = 🗜 Compress
dt-action-rotate = 🔄 Rotate pages
dt-action-images = 🖼 PDF → images
dt-images-format = Choose how to receive the PDF pages.
dt-images-zip = 📦 ZIP file
dt-images-album = 🖼 Photo album
dt-action-numbers = 🔢 Page numbers
dt-action-watermark = 💧 Watermark
dt-action-encrypt = 🔒 Lock PDF
dt-action-decrypt = 🔓 Unlock PDF
dt-action-image_pdf = 📑 Images → PDF
dt-action-enhance = ✨ Enhance scans
dt-action-ocr_text = 🔎 OCR → text
dt-action-ocr_docx = 📝 OCR → Word
dt-action-count = 🔢 Word/page count
dt-action-summarize = 📖 Summarize
dt-action-quiz = 🧠 Quiz me
dt-ask-split = Send page groups separated by semicolons, e.g. 1-2;3-5. Each group becomes a PDF. /cancel to stop.
dt-ask-extract = Send page ranges, e.g. 1-3,5. /cancel to stop.
dt-ask-rotate = Send the rotation in degrees: 90, 180 or 270. /cancel to stop.
dt-ask-watermark = Send the watermark text (up to 200 characters). /cancel to stop.
dt-ask-encrypt = Send a password (up to 127 UTF-8 bytes) to lock the PDF. Keep it safely. /cancel to stop.
dt-ask-decrypt = Send the PDF's password to unlock it. /cancel to stop.
dt-error-password = The password is missing, incorrect or too long. Try again with the correct PDF password.
dt-error-pages = This job exceeds your page limit, or the requested pages do not exist. Use fewer pages or /vip.
dt-error-invalid = This file or action is not supported. Send valid PDFs, images, DOCX or text and check the requested ranges.
dt-error-large = The files or generated output exceed your size limit. Use smaller files or /vip. Cloud Bot API downloads are capped at 20 MB.
dt-error-unavailable = AI or OCR is unavailable right now. Try later or use a non-AI PDF tool.
dt-error-quota = You reached today's AI action limit. Try after midnight UTC or open /vip.
dt-error-unknown = This job couldn't finish. Your action allowance was restored; please try again.
dt-error-queue = You already have the maximum number of queued/running jobs. Wait for a result and try again.
dt-error-basket = Your basket is full. Clear it or finish the current files first.
dt-job-expired = This queued job expired. Its action allowance was restored. Send your files again.
dt-admin-tab = 📚 Documents
dt-admin =
    📚 <b>Document tools</b>
    Jobs: { $total }
    Completed: { $ok }
    Failed: { $failed }
vip-perks = Larger document baskets (up to { $size } MB with a local Bot API server), { $pages } pages per job and { $ai } AI actions per day.
cmd-tools-desc = Your file basket
cmd-cite-desc = Format a DOI, ISBN or URL citation
cmd-count-desc = Count words, characters and pages
cmd-clear-desc = Clear your file basket
cmd-help-desc = Document tools help
