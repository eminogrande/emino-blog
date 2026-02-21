+++
title = "The Invisible Giants: 21 Developers Who Built Your Internet"
date = 2025-12-07T17:25:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "the-invisible-giants-21-developers-who-built-your-internet"
markup = "markdown"
body_format = "markdown"
+++

![](/media/the-invisible-giants-21-developers-who-built-your-internet/cover.jpg)

We often praise the founders of Facebook or Google, but the modern
internet is actually built on a foundation of open-source code
maintained by a small group of volunteers. These are the "Invisible
Giants." You likely use their code every single day without realizing
it.

Here is the story of the top 21, starting with the master of the file system.

### 1. The Watchman: Paul Millr
* **Handle:** [`@paulmillr`](https://github.com/paulmillr)
* **The Crown Jewel:** **[`chokidar`](https://github.com/paulmillr/chokidar)**
* **The Numbers:** Used in over **30 million** repositories; hundreds
of millions of downloads.
* **The Story:** In the early days of Node.js, the simple act of
"watching" a file for changes (so your app could reload automatically)
was broken. It was buggy, crashed on Macs, and ignored errors on
Windows. Paul didn't just accept this; he built **Chokidar**.
    **Why it’s special:** It solved the most painful part of the
developer experience: waiting. Every time you hit `Ctrl+S` in VS Code,
or your React app instantly updates in the browser, that is Paul’s
code running in the background, efficiently watching the world for
you.

---

### 2. The King of Productivity: Sindre Sorhus
* **Handle:** [`@sindresorhus`](https://github.com/sindresorhus)
* **The Crown Jewel:** **[`chalk`](https://github.com/chalk/chalk)**
* **The Numbers:** 1.9 Billion+ downloads.
* **The Story:** Sindre is a legend who believes in the "Unix
Philosophy": small modules that do one thing well. His most famous
creation, **Chalk**, brought color to the terminal.
    **Why it’s special:** Before Sindre, the terminal was a bleak,
black-and-white wall of text. He made errors red, warnings yellow, and
success green. He literally colored the developer's world, reducing
eye strain and confusion for millions.

### 3. The Master of Micro-Utils: Jon Schlinkert
* **Handle:** [`@jonschlinkert`](https://github.com/jonschlinkert)
* **The Crown Jewel:**
**[`micromatch`](https://github.com/micromatch/micromatch)**
* **The Numbers:** 1.3 Billion+ downloads.
* **The Story:** Jon is the master of "matching." If you have ever
typed `*.js` to find all JavaScript files, or `src/**/*.css` to find
styles, you are using Jon's logic.
    **Why it’s special:** His code is the invisible sorting machine
inside Webpack, Babel, and ESLint. He ensures that when you ask for a
file, the computer actually finds the right one.

### 4. The Partner in Code: Brian Woodward
* **Handle:** [`@doowb`](https://github.com/doowb)
* **The Crown Jewel:**
**[`handlebars-helpers`](https://github.com/helpers/handlebars-helpers)**
* **The Numbers:** 860 Million+ downloads.
* **The Story:** Often working in tandem with Jon Schlinkert, Brian
builds the glue that holds static sites together.
    **Why it’s special:** He provides the "helpers" that allow
templating engines to function—formatting dates, looping through data,
and automating repetitive HTML tasks. He is the reason your blog
generator works.

### 5. The Modernizer: Daniel Tschinder
* **Handle:** [`@danez`](https://github.com/danez)
* **The Crown Jewel:** **[`babel-plugin-transform...`](https://babeljs.io)**
* **The Numbers:** 774 Million+ downloads.
* **The Story:** Daniel is a core pillar of the **Babel** team. Babel
is the "time machine" of the web; it lets you write futuristic code
today and converts it into code that older browsers can understand.
    **Why it’s special:** Without Daniel, we would still be writing
archaic JavaScript (ES5). He allows the entire industry to move
forward without leaving users on older computers behind.

### 6. The Babel Keeper: Henry Zhu
* **Handle:** [`@hzoo`](https://github.com/hzoo)
* **The Crown Jewel:** **[`babel-core`](https://github.com/babel/babel)**
* **The Numbers:** 743 Million+ downloads.
* **The Story:** Henry is the face of open-source sustainability. As
the lead maintainer of Babel, he manages the compiler that powers
React, Vue, and Next.js.
    **Why it’s special:** He holds the keys to the kingdom. If Babel
breaks, the modern web breaks. His "package" is actually the peace of
mind that your code will run anywhere, on any device.

### 7. The Architect: Logan Smyth
* **Handle:** [`@loganfsmyth`](https://github.com/loganfsmyth)
* **The Crown Jewel:**
**[`babel-loader`](https://github.com/babel/babel-loader)**
* **The Numbers:** 739 Million+ downloads.
* **The Story:** Logan builds the bridges. He specializes in how Babel
talks to other tools, specifically Webpack.
    **Why it’s special:** He created the translation layer that
connects your build system to the compiler. He makes sure the complex
"pipeline" of modern web development flows smoothly without clogging.

### 8. The Father of NPM: Isaac Z. Schlueter
* **Handle:** [`@isaacs`](https://github.com/isaacs)
* **The Crown Jewel:**
**[`glob`](https://github.com/isaacs/node-glob)** (and created `npm`)
* **The Numbers:** 736 Million+ downloads.
* **The Story:** Isaac is royalty. He created **npm** itself. However,
his most downloaded package is **glob**, which teaches Node.js how to
find files on a hard drive using patterns.
    **Why it’s special:** He didn't just write a package; he built the
playground everyone else on this list is playing in. Every time you
run `npm install`, you are using his invention.

### 9. The AST Surgeon: Brian Ng
* **Handle:** [`@existentialism`](https://github.com/existentialism)
* **The Crown Jewel:** **[`babel-types`](https://github.com/babel/babel)**
* **The Numbers:** 685 Million+ downloads.
* **The Story:** Brian’s work allows software to "understand" other
software. He maintains the tools that dissect code into Abstract
Syntax Trees (ASTs).
    **Why it’s special:** His tools don't just read code; they
surgically alter it. This is what allows tools to automatically fix
your bugs or format your messy code.

### 10. The Server Savior: Doug Wilson
* **Handle:** [`@dougwilson`](https://github.com/dougwilson)
* **The Crown Jewel:** **[`express`](https://github.com/expressjs/express)**
* **The Numbers:** 668 Million+ downloads.
* **The Story:** If you have ever visited a website powered by
Node.js, it was likely running on Express. Doug has been the tireless
maintainer of the standard web framework for Node.
    **Why it’s special:** He keeps the internet running. From small
blogs to massive APIs, his code handles the request and sends the
response.

### 11. The Creator: Sebastian McKenzie
* **Handle:** [`@sebmck`](https://github.com/sebmck)
* **The Crown Jewel:** **[`yarn`](https://github.com/yarnpkg/yarn)**
(and created Babel)
* **The Numbers:** 632 Million+ downloads.
* **The Story:** Sebastian is a prodigy. He created Babel (originally
`6to5`) as a teenager and then created **Yarn**, a faster alternative
to npm.
    **Why it’s special:** He single-handedly dragged JavaScript from
the dark ages of 2009 into the modern era. He defined the workflow of
the 2010s.

### 12. The Evangelist: James Kyle
* **Handle:** [`@thejameskyle`](https://github.com/thejameskyle)
* **The Crown Jewel:** **[`flow`](https://flow.org/)** / Babel Plugins
* **The Numbers:** 625 Million+ downloads.
* **The Story:** James was the bridge between complex compilers and
regular humans. He wrote the manuals, the guides, and the plugins that
made tools like Babel and Flow accessible.
    **Why it’s special:** He turned "impossible" technology into
"easy-to-use" tools.

### 13. The Unicode Guardian: Mathias Bynens
* **Handle:** [`@mathias`](https://github.com/mathias)
* **The Crown Jewel:** **[`he`](https://github.com/mathias/he)** (HTML Entities)
* **The Numbers:** 481 Million+ downloads.
* **The Story:** Computers are bad at text, especially emojis and
weird symbols. Mathias is the world expert on how JavaScript handles
characters.
    **Why it’s special:** If you have ever used an emoji 🚀 in a
password or a username and the site didn't crash, thank Mathias. He
ensures the web speaks every human language correctly.

### 14. The Godfather: TJ Holowaychuk
* **Handle:** [`@tjholowaychuk`](https://github.com/tjholowaychuk)
* **The Crown Jewel:**
**[`commander`](https://github.com/tj/commander.js)** / `mocha`
* **The Numbers:** 364 Million+ downloads.
* **The Story:** The most prolific programmer in Node history. He
wrote the original versions of Express, Mocha, and Commander.
    **Why it’s special:** He defined the "style" of Node.js. If you
write code that looks clean and elegant, you are likely mimicking TJ’s
style.

### 15. The Philosopher: James Halliday
* **Handle:** [`@substack`](https://github.com/substack)
* **The Crown Jewel:**
**[`minimist`](https://github.com/substack/minimist)** / `browserify`
* **The Numbers:** 417 Million+ downloads.
* **The Story:** "Substack" invented the idea that you could write
Node.js code and run it in the browser. He created **Browserify**.
    **Why it’s special:** He started the revolution of "bundling" that
leads directly to the modern tools we use today.

### 16. The Performance Obsessive: John-David Dalton
* **Handle:** [`@jdalton`](https://github.com/jdalton)
* **The Crown Jewel:** **[`lodash`](https://github.com/lodash/lodash)**
* **The Numbers:** 375 Million+ downloads.
* **The Story:** JD Dalton realized the standard JavaScript library
was too slow and incomplete. He built **Lodash**, a utility belt that
became the most depended-upon library in history.
    **Why it’s special:** He was obsessed with speed. His functions
were often faster than the browser's built-in ones.

### 17. The Command Line Commander: Ben Coe
* **Handle:** [`@bcoe`](https://github.com/bcoe)
* **The Crown Jewel:** **[`yargs`](https://github.com/yargs/yargs)**
* **The Numbers:** 310 Million+ downloads.
* **The Story:** Ben makes the command line friendly. He maintains
**Yargs**, the tool that parses command line arguments.
    **Why it’s special:** Every time you type a command like `--help`
or `--version`, Ben’s code figures out what you mean and tells the
program what to do.

### 18. The Polyfill King: Jordan Harband
* **Handle:** [`@ljharb`](https://github.com/ljharb)
* **The Crown Jewel:**
**[`object.assign`](https://github.com/ljharb/object.assign)**
* **The Numbers:** 279 Million+ downloads.
* **The Story:** Jordan ensures backward compatibility. He maintains
hundreds of "polyfills"—shims that teach old browsers new tricks.
    **Why it’s special:** He fights for the users on old computers,
ensuring the web remains accessible to everyone, not just those with
the newest MacBooks.

### 19. The Stream Master: Dominic Tarr
* **Handle:** [`@dominictarr`](https://github.com/dominictarr)
* **The Crown Jewel:** **[`through`](https://github.com/dominictarr/through)**
* **The Numbers:** 279 Million+ downloads.
* **The Story:** Dominic is a mad scientist of data streams. He wrote
the tools that allow data to flow through applications like water
through pipes.
    **Why it’s special:** He championed the idea of "small modules"
more than anyone else, creating a massive network of tiny, perfect
tools.

### 20. The Plumber: Nathan Rajlich
* **Handle:** [`@tootallnate`](https://github.com/TooTallNate)
* **The Crown Jewel:** **[`node-gyp`](https://github.com/nodejs/node-gyp)**
* **The Numbers:** 224 Million+ downloads.
* **The Story:** Nathan handles the heavy lifting. He maintains the
tools that let Node.js talk to C++ and low-level system components.
    **Why it’s special:** He bridges the gap between the "easy" world
of JavaScript and the "hard" world of machine code.

### 21. The P2P Pioneer: Feross Aboukhadijeh
* **Handle:** [`@feross`](https://github.com/feross)
* **The Crown Jewel:**
**[`standard`](https://github.com/standard/standard)** / `webtorrent`
* **The Numbers:** 206 Million+ downloads.
* **The Story:** Feross is a visionary who wants to make the web
decentralized. He built **WebTorrent** (BitTorrent in the browser) and
**Standard** (a linter that bans semicolons).
    **Why it’s special:** He proves that JavaScript can do
anything—even stream movies peer-to-peer directly in your browser
without a plugin. He pushes the boundaries of what is possible in a
web browser.

---
*Post created via email from emin@nuri.com*
