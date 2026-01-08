# The Grid.

**Time is finite. Your wallpaper was wasting it.**

I built a dynamic engine that visualizes the passage of time. It doesn't just "show the date." It forces you to witness the decay of the current year, quarter, month, or fortnight in real-time.

It’s minimalist. It’s automated. It’s better than whatever photo of a sunset you’re currently using.

---

## 👁️ The Upgrade

We used to run this on a static script. It was fine. "Fine" is for mediocrity.

We rewrote the entire architecture. **The Grid** is now a fully dynamic Python application running on Vercel. It uses `Pillow` to render pixel-perfect, mathematically centered geometry on the fly.

No more waiting for midnight GitHub Actions. You want a grid? You get it now.

## 🎛️ The Features

We over-engineered it. You're welcome.

* **Dynamic Geometry:** Whether you view a 365-day Year or a 14-day Fortnight, the dots resize and center themselves automatically.
* **View Modes:** Year, Quarter, Month, Fortnight. Choose your preferred anxiety horizon.
* **Theme Engine:** Dark Mode (Correct). Light Mode (Incorrect, but supported).
* **Progress Bars:** Segmented, Solid, or Minimal. Because you care about lines.
* **Signatures:** Add your name. Add a quote. Add your battery percentage. We used a custom script font so it looks like you signed it yourself. You didn't.
* **Platform Gating:** **iOS & macOS Only.** If you are on Android, the site will politely tell you to leave. We care about the ecosystem. You should too.

---

## 📲 The Protocol

This isn't a "widget." Widgets drain battery. This is a **Wallpaper Automation**.

We built an iOS Shortcut that talks to our API, generates your custom grid, and sets it as your lock screen background without you lifting a finger.

### Phase 1: Configuration

1.  Open [The Grid](https://the-day-grid.vercel.app/) on your iPhone.
2.  **Customize it.** Pick your mode. Pick your theme. Add the dates that actually matter to you.
3.  Click **"Generate Custom Link."**
4.  If you changed nothing, we *will* mock you. If you did it right, we’ll copy the URL to your clipboard.

### Phase 2: The Shortcut

Download the tool that does the heavy lifting.

👉 **[Install the iOS Shortcut](https://www.icloud.com/shortcuts/99a190f4001844f9ade585fc8eafd47e)**

* **Important:** When you install it, it will ask for a URL. **Paste the URL you copied in Phase 1.**
* *Note:* If you messed this up, tap the three dots `(...)` on the shortcut, scroll down to the Text box, and paste your URL there. Don't break anything else.

### Phase 3: Automation (Set & Forget)

You have a supercomputer in your pocket. Make it work for you.

1.  Open the **Shortcuts** app.
2.  Tap the **Automation** tab at the bottom.
3.  Tap **New Automation** (or the **+** icon).
4.  Select **Time of Day**.
5.  Set it to **00:01** (or whenever you wake up). Ensure **"Run Immediately"** is checked. **Do not** let it "Ask Before Running." That defeats the purpose.
6.  Tap **Next**.
7.  Select the **The Grid** shortcut you just installed.
8.  Tap **Done**.

**Congratulations.**
Every morning, while you are asleep, your phone will reach out to our server, render a new visualization of your remaining time, and apply it to your screen.

---

## 🎨 The Legend

We used colors. Try to keep up.

* ⚪ **White:** The Past. Gone. Irrelevant.
* 🟠 **Orange:** The Present. You are here. Panic accordingly.
* 🟡 **Yellow:** Special Dates. The deadlines you're going to miss.
* ⚫ **Gray:** The Future. The Void.

---

## 🛠️ Tech Stack

* **Backend:** Python (Flask)
* **Imaging:** PIL (Python Imaging Library)
* **Font:** Roboto & Buffalo (Custom Script)
* **Hosting:** Vercel (Serverless)
* **Price:** Free. For now.

---

*&lt;/&gt; with ☕ and zero patience by [Spandan](https://github.com/the-rebooted-coder).*
