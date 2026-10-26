# Mac play-test checklist

The Mac build (Apple Silicon, macOS 11 or later) is made by the release workflow, and appears on the next release you tag as `PhilosophersQuest-<version>-macOS-arm64.zip`.

- **Already checked automatically.** Before the release publishes, the workflow launches the built Mac app headless and proves it can save, reload and restore a game, and seal a Seeker profile with the real key.
- **What only a person on the Mac can check:** everything below.

## 1. Get it running (once)

1. Check that the Mac is Apple Silicon: Apple menu → **About This Mac** should say **Chip: Apple M1** (or M2, M3...). An Intel Mac cannot run this build.
2. On the release page, download `PhilosophersQuest-<version>-macOS-arm64.zip`. Safari unzips it; otherwise double-click the zip.
3. Drag **PhilosophersQuest** into **Applications**.
4. Open it. macOS says it cannot verify the app.
   - Click **Done** (not Move to Trash).
   - Open **System Settings → Privacy & Security**, scroll down, click **Open Anyway** next to PhilosophersQuest, and confirm with your password or Touch ID.
5. Quit it and open it again from Applications.
   - [ ] It opens with no warning the second time.

## 2. The window and the keys

- [ ] **Window size.** The window is a sensible size on the screen, and text is sharp enough to read. Nothing is cut off at the edges.
- [ ] **Full screen.** The green button in the window's top-left corner goes full screen and back.
  - On a Mac keyboard **F11** shows the desktop instead, so the game's full-screen key is **fn + F11**.
  - To make F-keys work without fn: System Settings → Keyboard → Keyboard Shortcuts → Function Keys → "Use F1, F2, etc. keys as standard function keys".
- [ ] **Sound.** Sound plays, and **fn + F10** turns it on and off.
- [ ] **Everyday keys.** In a short game, try these: arrows, the letter commands, `\` (pray), `;`, `@` (Shift + 2), `?` (help), and Esc.
- [ ] **Scrolling a long quiz.** **fn + ↑ / fn + ↓** act as Page Up / Page Down.
- [ ] **No permission prompt.** At no point does macOS ask whether the game may "access files in your Documents folder".

## 3. Saving and the Seeker profile

1. On the title screen, choose or create a **Seeker**. Start a hero and play a few minutes: cook something, open a chest, go down a stair.
2. Quit with **Cmd + Q** (or close the window).
3. Open the game again.
   - [ ] **Continue** brings back the same hero, on the same floor, with the same items.
   - [ ] The Seeker is still there, and its profile (title screen, **F4**, i.e. **fn + F4**) still shows its progress.
4. In Finder, choose **Go → Go to Folder…** and paste `~/Library/Application Support/PhilosophersQuest`.
   - [ ] It holds a `save_….pkl` file and a `seekers` folder.

## 4. If anything goes wrong

The error log is at `~/Library/Logs/PhilosophersQuest/ERROR_LOG.txt` (Finder → Go → Go to Folder…). Send it along with a note of what you did and what you saw.

## Known limits

- **Unsigned.** The "Open Anyway" step is needed once on every Mac. Removing it needs an Apple Developer account ($99 a year), with signing and Apple's check added to the release.
- **Apple Silicon only.** There is no Intel build.
