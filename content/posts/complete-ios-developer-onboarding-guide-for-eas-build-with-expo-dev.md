+++
title = "Complete iOS Developer Onboarding Guide for EAS Build with Expo.dev"
date = 2025-08-29T07:15:02Z
draft = false
author = "Emino"
tags = ["email-post", "photos"]
categories = ["blog"]
+++

![](/media/complete-ios-developer-onboarding-guide-for-eas-build-with-expo-dev/cover.jpg)

# Complete iOS Developer Onboarding Guide for EAS Build

## Phase 1: Company Admin Setup (You Do This First)

### 1. Add Developer to Apple Developer Account
- Go to https://developer.apple.com
- Click "Users and Access"
- Click "+" button
- Enter developer's email
- Select "Admin" or "Developer" role
- Click "Invite"

### 2. Add Developer to App Store Connect
- Go to https://appstoreconnect.apple.com/access/users
- Click "+" button
- Enter same email as above
- Select appropriate role (Developer/Admin/App Manager)
- Click "Invite"

### 3. Add Developer to Expo Organization
- Go to https://expo.dev
- Navigate to Settings → Members
- Click "Invite Member"
- Enter developer's email
- Select "Developer" or "Admin" role
- Send invitation

### 4. Get Developer's Device UDID
- Ask developer to go to: Settings → General → About
- Tap and hold "Serial Number" until "UDID" appears
- Have them send you the UDID string

### 5. Register Device in Apple Developer Portal
- Go to https://developer.apple.com
- Navigate to "Devices" section
- Click "+" to add device
- Enter name (e.g., "John's iPhone 14")
- Enter the UDID
- Save

### 6. Share Repository Access
- Add developer to GitHub/GitLab/Bitbucket
- Grant appropriate permissions
- Share repository URL

## Phase 2: Developer Account Setup (Developer Does This)

### 7. Accept Apple Developer Invitation
- Check email for Apple invitation
- Click accept link
- Sign in with personal Apple ID (or create one)
- Accept terms and conditions

### 8. Accept App Store Connect Invitation
- Check email for App Store Connect invitation
- Click accept link
- Sign in with same Apple ID
- Accept terms

### 9. Create and Setup Expo Account
- Go to https://expo.dev
- Create account with same email
- Verify email address
- Accept organization invitation from email

### 10. Setup Development Environment
- Install Node.js (v16 or higher)
- Install Git
- Install VS Code or preferred editor
- Open terminal/command prompt

### 11. Install Required CLI Tools
```bash
npm install -g expo-cli
npm install -g eas-cli
```

### 12. Login to Expo/EAS
```bash
eas login
# Enter personal Expo credentials (not company's)
```

### 13. Clone and Setup Project
```bash
git clone [repository-url]
cd [project-name]
npm install
```

## Phase 3: First Development Build

### 14. Verify EAS Configuration
```bash
# Check that eas.json exists and has development profile
cat eas.json
```

### 15. Create Development Build
```bash
eas build --profile development --platform ios
```
- EAS automatically uses company's stored credentials
- Wait for build to complete (10-20 minutes)
- Build appears in Expo dashboard

## Phase 4: Device Setup (Developer's iPhone)

### 16. Enable Developer Mode (iOS 16+)
- Settings → Privacy & Security
- Scroll to "Developer Mode" (won't appear until step 17 fails first)
- Toggle ON
- Device will restart
- After restart: confirm "Turn On Developer Mode"
- Enter device passcode

### 17. Install Development Build
- Open EAS dashboard in Safari on iPhone
- Or get direct link from terminal after build completes
- Tap "Install" on the build
- If Developer Mode not enabled, it will fail (go back to step 16)

### 18. Trust Developer Certificate
- Go to Settings → General → VPN & Device Management
- Find profile under "Developer App"
- Tap company name profile
- Tap "Trust [Company Name]"
- Confirm trust

### 19. Launch App
- App icon appears on home screen
- Tap to open
- App should run successfully

## Phase 5: Daily Development Workflow

### 20. Start Development Server
```bash
# In project directory
npx expo start --dev-client
```

### 21. Connect Device to Development Server
- Ensure iPhone and computer on same WiFi
- Open installed app on iPhone
- App connects to Metro bundler
- See live updates as you code

### 22. Creating New Builds
```bash
# Development build (for testing)
eas build --profile development --platform ios

# Preview build (for internal testing)
eas build --profile preview --platform ios

# Production build (for App Store)
eas build --profile production --platform ios
```

### 23. Submitting to TestFlight
```bash
# After production build completes
eas submit -p ios
```

## Phase 6: Troubleshooting Checklist

### 24. If Build Won't Install
- ✓ Check UDID is registered in Apple Developer
- ✓ Check Developer Mode is enabled
- ✓ Check device management trust settings
- ✓ Rebuild with `--clear-cache` flag

### 25. If Can't Access Expo Project
- ✓ Verify logged into correct Expo account
- ✓ Check organization membership accepted
- ✓ Run `eas whoami` to verify identity

### 26. If Build Fails
- ✓ Check Apple Developer access is active
- ✓ Verify eas.json configuration
- ✓ Check bundle ID matches Apple settings
- ✓ Review build logs in EAS dashboard

## Required Information Summary

**Developer Needs From You:**
- Repository URL
- Project name
- Which branch to use
- Any ENV variables or secrets

**You Need From Developer:**
- Email address
- iPhone UDID
- Confirmation when invitations accepted

**Automatic via EAS:**
- All certificates
- Provisioning profiles
- Code signing
- Bundle ID configuration

**No Mac Required!** Everything works on Windows/Linux through EAS Build
cloud service.


---
*This post was created via email by emin@nuri.com*
