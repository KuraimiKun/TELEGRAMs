**S01 Introduction — phase0; spec specified except explicit questions/defects; implementation not applicable.** https://missrose.org/docs/

Behavior IDs S01-Bnn: B01 [not applicable; specified] Navigation page: denominator only → Account for all 50 navigation pages without inventing a moderation command.

**S02 Getting started — phase0; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/getting-started/

Behavior IDs S02-Bnn: B01 [partial; specified] Add-to-group entry uses runtime bot identity → Use a different test username and inspect the link; B02 [partial; specified] Onboarding explains required administrative rights → An unprivileged bot describes missing rights without promising enforcement.

**S03 Before you start — phase0; spec specified except explicit questions/defects; implementation not applicable.** https://missrose.org/docs/basics/

Behavior IDs S03-Bnn: B01 [not applicable; specified] Orientation: username resolution is limited → Unknown username returns clear error and reply/ID alternatives, never a guessed user.

**S04 Command usage — phase1; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/basics/command-usage/

Behavior IDs S04-Bnn: B01 [partial; specified] Group and connected PM select the same target group → Compare one setting through both entry points; B02 [partial; specified] Boolean on/yes/true and off/no/false → Accept each spelling with identical stored boolean; B03 [partial; specified] Common durations m/h/d/w plus legacy seconds extension → Validate units separately from module-specific bounds.

S04-BOOL-TOKEN IDs (on yes true off no false); Boolean synonym; phase1; implementation {partial: on,yes,true,off,no,false}; acceptance: Parse to the stated boolean without changing unrelated fields

S04-DURATION-TOKEN IDs (m h d w s); Duration suffix (s retained extension); phase1; implementation {partial: m,h,d,w,s}; acceptance: Valid bounded value parses; invalid/boundary rejects without permanent fallback

**S05 Info — phase2; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/basics/info/

Commands /id, /info; spelling IDs GG-CMD-id, S05-C-info. Behavior IDs S05-Bnn: B01 [partial; specified] ID self/current group/reply/known username → Each form returns the intended identity, distinguish negative chat IDs; B02 [not implemented; specified] Info self/reply/known username/ID with available profile membership and fedban → Show available fields and clear unavailable-data errors.

Variants: S05-V-id-self-reply-username [partial; specified] `/id self/current group/reply/@known` → Each form returns correct ID without arbitrary username inference; S05-V-info-target [not implemented; specified] `/info self/reply/@known/ID` → Return available fields for exact target

S06: S06-PAGE, introduction only; same S40 connection implementation, both references. Acceptance: one connection service. Phase8 for implementation; page Phase0; spec specified, implementation not applicable.

**S07 Languages — phase11; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/basics/languages/

Commands /setlang; spelling IDs S07-C-setlang. Behavior IDs S07-Bnn: B01 [not implemented; specified] Selector and direct locale code affect group/connected responses → Same selected language through group and PM paths; B02 [partial; specified] English-only Rose start/help with localized GroupGuard help retained → Preserve existing Arabic/English help and label enhancement; B03 [partial; specified] Locale fallback is not translation parity → Audit keys and rendered text independently for every locale.

S07-LANG-TOKEN IDs (AR AZ BE BG CKB DE EN-GB EN-PT ES ES-AR FA FIL FR HE ID IT ML-IN MS NL PL PT PT-BR RU SH TA TR UK UZ VI ZH-CN ZH-TW); Published locale; phase11; implementation {existing-unverified: AR; not implemented: AZ,BE,BG,CKB,DE,EN-GB,EN-PT,ES,ES-AR,FA,FIL,FR,HE,ID,IT,ML-IN,MS,NL,PL,PT,PT-BR,RU,SH,TA,TR,UK,UZ,VI,ZH-CN,ZH-TW}; acceptance: Select exact code; independently audit required translations, no fallback-only parity

Variants: S07-V-setlang-code [not implemented; specified] `/setlang CODE` → Select group language; invalid code errors

**S08 Rules — phase3; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/basics/rules/

Commands /rules, /setrules, /resetrules, /privaterules, /setrulesbutton, /resetrulesbutton; spelling IDs GG-CMD-rules, GG-CMD-setrules, S08-C-resetrules, S08-C-privaterules, S08-C-setrulesbutton, S08-C-resetrulesbutton. Behavior IDs S08-Bnn: B01 [partial; specified] Rules formatted read/set/reset → Read stored formatting after update and reset content without changing access policy; B02 [partial; specified] Group delivery versus PM-opening rules button → Toggle privateness and assert actual delivery; B03 [not implemented; specified] Rules button custom/reset label and {rules} filling → Render custom then default label in supported content; B04 [partial; specified] Public rules access is separate from change-info mutation → Deny settings mutation to member while allowing rules access.

**S09 Administrator permissions — phase2; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/moderation/admins/

Commands /promote, /demote, /adminlist, /adminerror, /admincache, /anonadmin; spelling IDs S09-C-promote, S09-C-demote, S09-C-adminlist, S09-C-adminerror, S09-C-admincache, S09-C-anonadmin. Behavior IDs S09-Bnn: B01 [partial; specified] Exact caller and bot rights for each operation → Deny unrelated-admin right for settings/delete/restrict/pin/promote/topics; B02 [not implemented; specified] Promote caller/bot intersection excluding promote-members → No newly promoted user gains promotion right; B03 [not implemented; specified] Demote only bot-editable appropriate admin role → Reject non-editable admin target; B04 [not implemented; specified] Public adminlist omits anonymous admins → No anonymous identity disclosed; B05 [not implemented; specified] Permission-error toggle is separate from authorization → Off hides error but still denies mutation; B06 [not implemented; specified] Admincache refresh invalidates stale admin list → Demotion then refresh removes authority; B07 [not implemented; specified] Anonymous default identifies human through button and checks actual rights → Unidentified group sender cannot mutate; B08 [not implemented; specified] anonadmin on assumes admin rights but excludes owner → Owner-only operation still denied; B09 [partial; specified] Owner-only operations require attributable creator → Platform/factory/admin/channel identity never substitutes for group creator.

S09-RIGHT-TOKEN IDs (change_info delete_messages restrict_members pin_messages promote_members manage_topics creator); Permission mapping; phase1; implementation {partial: change_info,delete_messages,restrict_members,pin_messages,creator; not implemented: promote_members,manage_topics}; acceptance: Correct caller and bot capability; unrelated admin right denied; creator always attributable

**S10 Pins — phase2; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/moderation/pins/

Commands /pin, /permapin, /unpin, /unpinall, /antichannelpin, /cleanlinked; spelling IDs GG-CMD-pin, S10-C-permapin, GG-CMD-unpin, S10-C-unpinall, S10-C-antichannelpin, S10-C-cleanlinked. Behavior IDs S10-Bnn: B01 [partial; specified] Reply pin is quiet by default and loud requests notification → Assert Telegram disable_notification in both modes; B02 [not implemented; specified] Permapin sends formatted content then pins that new message → No periodic repin scheduler created; B03 [partial; specified] Unpin latest or replied pin and unpinall → Assert correct target/API for each variant; B04 [not implemented; specified] Automatic linked-channel post unpin → Leave generic forward unaffected; B05 [not implemented; specified] Cleanlinked deletes discussion auto-forward → Delete only linked-channel-origin post.

Variants: S10-V-pin-loud [partial; specified] `/pin loud` → disable_notification=False

**S11 Approvals — phase2; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/moderation/approvals/

Commands /approve, /approval, /approved, /unapprove, /unapproveall; spelling IDs S11-C-approve, S11-C-approval, S11-C-approved, S11-C-unapprove, S11-C-unapproveall. Behavior IDs S11-Bnn: B01 [not implemented; specified] Approve usual target with optional reason and status lookup → Resolve reply/ID/known username and round-trip reason; B02 [not implemented; specified] Large approval list delivered as file → Bound chat output and verify file contents; B03 [not implemented; specified] Unapproveall creator-only → Ordinary admin cannot clear all; B04 [not implemented; specified] Approved users exempt from automated actions with manual authority separate → Approved target still subject to authorized manual ban; B05 [not implemented; unresolved edge] Federation/newcomer/raid approval precedence unspecified → Require explicit policy before implementing exemptions.

**S12 Purges — phase2; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/moderation/purges/

Commands /del, /purge, /spurge, /purgefrom, /purgeto; spelling IDs GG-CMD-del, GG-CMD-purge, S12-C-spurge, S12-C-purgefrom, S12-C-purgeto. Behavior IDs S12-Bnn: B01 [partial; specified] Reply del deletes target and command with no completion message → Inspect both deletes and absence of acknowledgement; B02 [partial; specified] Reply purge selects start through command → Assert inclusive endpoints; B03 [not implemented; specified] Purge N starts at reply and selects N messages → Assert count and operational cap; B04 [partial; specified] Non-reply purge-all absent → Reject no-reply purge; B05 [not implemented; specified] Spurge suppresses completion → No group confirmation while retaining truthful result; B06 [not implemented; specified] Two-step endpoints bind actor/chat → Wrong actor/chat cannot finish range; B07 [partial; specified] Deletion limits and API acknowledgement require truthful counts → Do not report submitted IDs as confirmed deleted count.

Variants: S12-V-purge-N [not implemented; specified] `/purge N (reply)` → N messages start at reply and respect cap

**S13 Admin logs — phase2; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/moderation/log-channels/

Commands /setlog, /unsetlog, /logchannel, /logcategories, /log, /nolog; spelling IDs GG-CMD-setlog, GG-CMD-unsetlog, S13-C-logchannel, S13-C-logcategories, S13-C-log, S13-C-nolog. Behavior IDs S13-Bnn: B01 [not implemented; specified] Channel setlog original command forwarded to group establishes destination → Bot is channel admin, authenticate source/destination, reject fabricated forward; B02 [partial; specified] Authorized numeric setlog remains extension → Retain existing shortcut without bypassing permission checks; B03 [partial; specified] Multiple groups can share one destination → Each group remains independently authorized; B04 [not implemented; specified] Log category toggles all enabled by source default → Toggle one category without overwriting others or live-group defaults; B05 [not implemented; specified] Leave logs stop at 50 members → Test 49/50/51 boundary; B06 [partial; specified] Log delivery failure distinct from sanction → No successful audit-delivery claim when send fails.

S13-LOG-TOKEN IDs (settings admin user automated reports other); Log category, source default enabled; phase2; implementation {not implemented: settings,admin,user,automated,reports,other}; acceptance: Toggle this category independently and verify permitted matching event reaches log

**S14 Restrictions — phase2; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/moderation/restrictions/

Commands /ban, /tban, /dban, /sban, /unban, /mute, /tmute, /dmute, /smute, /unmute, /kick, /dkick, /skick; spelling IDs GG-CMD-ban, GG-CMD-tban, S14-C-dban, GG-CMD-sban, GG-CMD-unban, GG-CMD-mute, GG-CMD-tmute, S14-C-dmute, S14-C-smute, GG-CMD-unmute, GG-CMD-kick, S14-C-dkick, S14-C-skick. Behavior IDs S14-Bnn: B01 [partial; specified] Targets reply/known username/ID with optional reason → Unknown identity fails and negative chat ID is not a user target; B02 [partial; specified] Temporary aliases require a valid bounded duration → Missing/invalid/zero/short/overlong time never becomes permanent; B03 [not implemented; specified] Delete-and-act variants require reply → Reject dban/dmute/dkick without reply; B04 [partial; specified] Manual silent removes reply if present and command, suppresses confirmation → Inspect deletion/sanction/log independently without automated gate; B05 [partial; specified] Kick removal allows rejoin → Ban then unban failure reports partial outcome; B06 [partial; specified] Unban and unmute report real API outcome → Mock failure cannot produce success; B07 [partial; specified] Target bot/admin protection and precise capability checks → Reject protected target and missing caller/bot rights.

**S15 Warnings — phase2; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/moderation/warnings/

Commands /warnings, /setwarnlimit, /setwarnmode, /warn, /dwarn, /swarn, /rmwarn, /resetwarn, /warns, /setwarntime, /warntime; spelling IDs S15-C-warnings, S15-C-setwarnlimit, S15-C-setwarnmode, GG-CMD-warn, S15-C-dwarn, S15-C-swarn, GG-CMD-rmwarn, S15-C-resetwarn, GG-CMD-warns, S15-C-setwarntime, S15-C-warntime. Behavior IDs S15-Bnn: B01 [partial; specified] Warnings settings versus user reasons list → Both public read forms return intended data; B02 [partial; specified] Warning normal/delete/silent message effects → Inspect command/reply deletion and acknowledgement separately; B03 [partial; specified] Latest warning removal versus button removal of one warning → Button cannot remove unrelated newer warning; B04 [partial; specified] User reset clears all user warnings → Scope to bot/chat/user; B05 [not implemented; specified] Per-warning age expiry and off disabling expiry → Different issue times expire independently; B06 [partial; specified] Successful threshold sanction resets warnings, failed sanction retains history → Mock API denial must not clear warnings; B07 [partial; unresolved edge] Limit versus going-over threshold ambiguous → Separate exact-limit and above-limit cases for decision; B08 [not implemented; unresolved edge] setwarntime versus example warntime unresolved alias → Do not claim exact spelling parity before decision.

S15-MODE-TOKEN IDs (kick ban mute tban tmute); Warning threshold action; phase2; implementation {partial: kick,ban,mute; not implemented: tban,tmute}; acceptance: Correct API/deadline; failed sanction retains warning state

**S16 Reports — phase2; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/moderation/reports/

Commands /reports, /report; spelling IDs S16-C-reports, GG-CMD-report. Behavior IDs S16-Bnn: B01 [not implemented; specified] Reports enabled by source default → Keep live-group defaults, enable new-group policy only explicitly; B02 [partial; specified] Reply report and @admin notify admins → Same reported target and anonymous privacy; B03 [partial; specified] Local /admin and /admins aliases avoid platform private UI → Group report cannot open platform admin controls.

**S17 Disabled commands — phase8; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/moderation/disabling/

Commands /disabled, /disableable, /disable, /enable, /disabledel, /disableadmin; spelling IDs S17-C-disabled, S17-C-disableable, S17-C-disable, S17-C-enable, S17-C-disabledel, S17-C-disableadmin. Behavior IDs S17-Bnn: B01 [not implemented; specified] None disabled by source default → Existing groups retain current settings; B02 [not implemented; specified] Disabled commands ignored with optional delete → Verify no command side effect and configured deletion; B03 [not implemented; specified] Disableadmin includes admins but recovery remains available → Privileged admin can restore settings; B04 [not implemented; specified] Catalog membership does not define command execution → Keep runs/saved/antiflood/kickme semantics open when only catalog evidence.

S17-DISABLE-TOKEN IDs (adminlist antiflood approval connect fedadmins fedinfo fedsubs filters flood id info kickme locks locktypes notes rules runs saved warnings warns); Disableable catalog name; phase8; implementation {not implemented: adminlist,approval,connect,fedadmins,fedinfo,fedsubs,filters,flood,id,info,locks,locktypes,notes,rules,warnings,warns; open meaning: antiflood,kickme,runs,saved}; acceptance: Catalog includes exact token; disabling suppresses its defined execution or remains explicit open meaning

**S18 Welcomes — phase3; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/greetings/

Commands /welcome, /setwelcome, /resetwelcome; spelling IDs S18-C-welcome, GG-CMD-setwelcome, GG-CMD-resetwelcome. Behavior IDs S18-Bnn: B01 [not implemented; specified] Welcome show/boolean/noformat variants → Each variant inspects or changes only intended state; B02 [partial; specified] Set welcome text or replied media/sticker optional caption → Preserve file/content identity and render fillings; B03 [partial; specified] Reset content separate from enable/verification state → Reset does not silently disable CAPTCHA; B04 [partial; specified] Canonical chatname and existing group/count fillings → Render each with event context, retain legacy HTML.

Variants: S18-V-welcome-show [not implemented; specified] `/welcome ` → Assert show affects only intended enable/content/inspection behavior; S18-V-welcome-on [not implemented; specified] `/welcome on` → Assert on affects only intended enable/content/inspection behavior; S18-V-welcome-yes [not implemented; specified] `/welcome yes` → Assert yes affects only intended enable/content/inspection behavior; S18-V-welcome-true [not implemented; specified] `/welcome true` → Assert true affects only intended enable/content/inspection behavior; S18-V-welcome-off [not implemented; specified] `/welcome off` → Assert off affects only intended enable/content/inspection behavior; S18-V-welcome-no [not implemented; specified] `/welcome no` → Assert no affects only intended enable/content/inspection behavior; S18-V-welcome-false [not implemented; specified] `/welcome false` → Assert false affects only intended enable/content/inspection behavior; S18-V-welcome-noformat [not implemented; specified] `/welcome noformat` → Assert noformat affects only intended enable/content/inspection behavior

**S19 Goodbyes — phase3; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/greetings/goodbyes/

Commands /goodbye, /setgoodbye, /resetgoodbye; spelling IDs S19-C-goodbye, S19-C-setgoodbye, S19-C-resetgoodbye. Behavior IDs S19-Bnn: B01 [not implemented; specified] Goodbye show/boolean/noformat variants → Each form preserves unrelated state; B02 [not implemented; specified] Text/replied media/sticker optional caption and reset → Round-trip payload; B03 [partial; specified] Leaving user identity comes from event → Service sender differing from departing user still fills departed user.

Variants: S19-V-goodbye-show [not implemented; specified] `/goodbye ` → Assert show affects only intended enable/content/inspection behavior; S19-V-goodbye-on [not implemented; specified] `/goodbye on` → Assert on affects only intended enable/content/inspection behavior; S19-V-goodbye-yes [not implemented; specified] `/goodbye yes` → Assert yes affects only intended enable/content/inspection behavior; S19-V-goodbye-true [not implemented; specified] `/goodbye true` → Assert true affects only intended enable/content/inspection behavior; S19-V-goodbye-off [not implemented; specified] `/goodbye off` → Assert off affects only intended enable/content/inspection behavior; S19-V-goodbye-no [not implemented; specified] `/goodbye no` → Assert no affects only intended enable/content/inspection behavior; S19-V-goodbye-false [not implemented; specified] `/goodbye false` → Assert false affects only intended enable/content/inspection behavior; S19-V-goodbye-noformat [not implemented; specified] `/goodbye noformat` → Assert noformat affects only intended enable/content/inspection behavior

**S20 Advanced greetings — phase8; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/greetings/advanced/

Commands /cleanwelcome; spelling IDs S20-C-cleanwelcome. Behavior IDs S20-Bnn: B01 [not implemented; specified] Old welcome message cleanup after fixed five minutes → Advance clock, only welcome messages expire; B02 [not implemented; specified] CAPTCHA/service-cleaning references point to existing source families → No duplicated implementation features.

**S21 Anti-spam overview — phase0; spec specified except explicit questions/defects; implementation not applicable.** https://missrose.org/docs/anti-spam/

Behavior IDs S21-Bnn: B01 [not applicable; specified] Anti-spam navigation only → Map locks/CAPTCHA/blocklist/flood/raid pages without extra commands.

**S22 Locks — phase5; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/anti-spam/locks/

Commands /locks, /locktypes, /lock, /unlock, /lockwarns, /allowlist, /rmallowlist, /rmallowlistall; spelling IDs GG-CMD-locks, S22-C-locktypes, GG-CMD-lock, GG-CMD-unlock, S22-C-lockwarns, S22-C-allowlist, S22-C-rmallowlist, S22-C-rmallowlistall. Behavior IDs S22-Bnn: B01 [not implemented; specified] Locks list versus locks list syntax and locktypes → Return configured and supported types separately; B02 [partial; specified] Multi-type lock/unlock with none locked by source default → Change only chosen types, preserve existing defaults; B03 [partial; specified] Admin exemption and locks before blocklists → Only intended first enforcement action occurs; B04 [not implemented; specified] Per-lock ### reason and {mode} override → Keep per-type reason/action separate from global defaults; B05 [not implemented; specified] Lockwarns warning integration → Warning result drives truthful feedback; B06 [not implemented; specified] rmallowlistall creator-only → Admin cannot clear all; B07 [not implemented; specified] Linked discussion comment/outsidereaction nonmember detection → Resolve actual membership with API guarantees; B08 [not implemented; specified] Entity/Unicode/media/origin/reaction classifiers distinct → Negative neighboring type does not trigger typed lock.

S22-LOCK-TOKEN IDs (all album anonchannel audio bot button cashtag checklist cjk command comment contact cyrillic document email emoji emojicustom emojigame emojionly externalreply forward forwarduser forwardbot forwardchannel forwardstory game gif guestbot inline invitelink botlink location outsidereaction phone photo poll reaction rtl spoiler sticker stickeranimated stickerpremium text url video videonote voice zalgo); Typed lock; phase5; implementation {not implemented: all,album,anonchannel,button,cashtag,checklist,cjk,command,comment,contact,cyrillic,email,emoji,emojicustom,emojigame,emojionly,externalreply,forwarduser,forwardbot,forwardchannel,forwardstory,game,guestbot,inline,botlink,location,outsidereaction,phone,reaction,rtl,spoiler,stickeranimated,stickerpremium,text,zalgo; partial: audio,bot,document,forward,gif,invitelink,photo,poll,sticker,url,video,videonote,voice}; acceptance: Positive matching event locks; negative neighboring type unaffected; admin exempt; allowlist and precise rights honored

S22-ALLOW-TOKEN IDs (url-domain url-subdomain url-path button-domain button-subdomain button-path invite-exact invite-chat invite-username inline-bot sender-channel command stickerpack emojipack forwarded-identity); Typed allowlist; phase5; implementation {not implemented: url-domain,url-subdomain,url-path,button-domain,button-subdomain,button-path,invite-exact,invite-chat,invite-username,inline-bot,sender-channel,command,stickerpack,emojipack,forwarded-identity}; acceptance: Exact allowed scope exempt, neighboring domain/path/identity not accidentally exempt; owner-only all-clear

S22-MODE-TOKEN IDs (kick ban tban mute tmute); Per-lock action; phase5; implementation {not implemented: kick,ban,tban,mute,tmute}; acceptance: This lock chooses configured reason/action with strict temporary duration

Variants: S22-V-locks-list [not implemented; specified] `/locks list` → Configured types distinct from locktypes; S22-V-lock-reason [not implemented; specified] `/lock TYPE ### reason` → Only selected lock reason updated; S22-V-lock-action [not implemented; specified] `/lock TYPE {mode}` → Select exact action with duration when temporary; S22-V-stickerpack-shortcut [not implemented; specified] `stickerpack:<> (reply)` → Extract only replied sticker pack; S22-V-emojipack-shortcut [not implemented; specified] `emojipack:<> (reply)` → Extract exact custom emoji pack

**S23 CAPTCHA — phase4; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/anti-spam/captchas/

Commands /captcha, /captchamode, /setcaptchatext, /resetcaptchatext, /captchakick, /captchakicktime, /captcharules, /captchamutetime; spelling IDs S23-C-captcha, S23-C-captchamode, S23-C-setcaptchatext, S23-C-resetcaptchatext, S23-C-captchakick, S23-C-captchakicktime, S23-C-captcharules, S23-C-captchamutetime. Behavior IDs S23-Bnn: B01 [partial; specified] Button default, other modes open PM → Each challenge reaches correct destination and mode; B02 [partial; specified] Success releases verification mute and failure temporary ban → Release only this challenge restriction and preserve unrelated sanction; B03 [partial; specified] Unsolved stay muted or configured kick → Deadline follows issued settings snapshot; B04 [not implemented; specified] Remember success per group → Another group still requires verification; B05 [not implemented; specified] Admin kick resets remembered success, voluntary leave retains → Test distinct membership transitions; B06 [partial; specified] Welcomes required by source → Validate dependency without destroying saved content; B07 [not implemented; specified] Captcha label plaintext with no fillings → Literal braces remain literal; B08 [partial; specified] Join request PM then optional rules then approve/welcome → Require invite-users and bounded contact window; B09 [not implemented; specified] Captcha kick deadline default5m and bounds5m..1day → Test min/max/outside; B10 [not implemented; specified] Auto-release duration or off → Issued challenge independent of later settings edits; B11 [not implemented; specified] Challenge identity/deadline independent of unrelated sanction → Old callback cannot release or kick current generation.

S23-CAPTCHA-TOKEN IDs (button text math text2); Captcha mode; phase4; implementation {partial: button,math; not implemented: text,text2}; acceptance: Current immutable challenge accepts intended solution; wrong/old/user/chat/bot solution fails

Variants: S23-V-kicktime [not implemented; specified] `/captchakicktime TIME` → Reject outside bounds without rewriting issued challenges; S23-V-mutetime-off [not implemented; specified] `/captchamutetime off` → No scheduled release for new challenge; existing issued state independent

**S24 Blocklist management — phase6; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/anti-spam/blocklists/

Commands /addblocklist, /blocklist, /rmblocklist, /rmblocklistall; spelling IDs S24-C-addblocklist, GG-CMD-blocklist, S24-C-rmblocklist, S24-C-rmblocklistall. Behavior IDs S24-Bnn: B01 [partial; specified] Add word/quoted phrase/parenthesized comma triggers with shared reason → Preserve multiword and per-entry content; B02 [not implemented; specified] Blocklist no-args lists and arguments add alias → Explicit unambiguous grammar, retain local aliases; B03 [partial; specified] Remove single/phrase/multiple and creator-only clearall → No unintended substring deletion; B04 [not implemented; specified] Embedded per-entry action modifier → Round-trip modifier separate from trigger.

Variants: S24-V-blocklist-list-add [partial; specified] `/blocklist [trigger]` → Explicit grammar and alias tests; S24-V-multi-trigger [partial; specified] `/addblocklist (a,b) reason` → Quoted/parenthesized terms preserve boundaries and shared reason

**S25 Blocklist modes — phase6; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/anti-spam/blocklists/modes/

Commands /blocklistmode, /blocklistdelete; spelling IDs S25-C-blocklistmode, S25-C-blocklistdelete. Behavior IDs S25-Bnn: B01 [not implemented; specified] Nothing default still deletes → Matching message deleted without user sanction; B02 [not implemented; specified] Blocklistdelete off suppresses deletion but keeps selected action → Mode and delete toggle are independent; B03 [not implemented; specified] Common temporary durations and per-entry override → Invalid time fails and entry action overrides default.

S25-MODE-TOKEN IDs (nothing warn kick ban tban mute tmute); Default blocklist mode; phase6; implementation {not implemented: nothing,warn,kick,ban,tban,mute,tmute}; acceptance: Nothing still deletes; delete toggle independent; temporary values validated

**S26 Advanced blocklists — phase6; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/anti-spam/blocklists/advanced/

Commands /setblocklistreason, /resetblocklistreason; spelling IDs S26-C-setblocklistreason, S26-C-resetblocklistreason. Behavior IDs S26-Bnn: B01 [partial; specified] Full-word match with accent and repeated-space normalization → Avoid substring false positive and test normalized equivalent; B02 [not implemented; specified] Default reason set/reset with entry override → Entry reason wins then fallback; B03 [not implemented; specified] Silent per-entry action gated by S49, never default blocklist mode → Reject default silent mode; B04 [not implemented; unresolved edge] Declared lookalike prefix versus exact typo → Keep exact and lookalike separate, record canonical proposal; B05 [not implemented; unresolved edge] Declared username prefix versus inline prose typo → Observed username pattern is distinct from inline origin; B06 [not implemented; specified] Clone name/username evaluated on joins and speaking → No claim about unseen profile changes.

S26-TYPE-TOKEN IDs (stickerpack file forward inline prefix exact lookalike name username); Typed blocklist prefix; phase6; implementation {not implemented: stickerpack,file,forward,inline,prefix,exact,lookalike,name,username}; acceptance: Positive trigger and close negative tested; identity/origin/text namespaces kept separate

S26-WILDCARD-TOKEN IDs (question star doublestar escape); Pattern token; phase6; implementation {not implemented: question,star,doublestar,escape}; acceptance: ?=one nonspace; *=zero/more nonspace; **=anychars; backslash literal; test each token independently

Variants: S26-V-entry-action [not implemented; specified] `{action}` → Silent only with S49 and non-silent default mode; S26-V-reason-reset [not implemented; specified] `/resetblocklistreason` → Per-entry reasons remain unchanged

**S27 Antiflood — phase7; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/anti-spam/antiflood/

Commands /flood, /setflood, /setfloodtimer, /setfloodmode, /clearflood; spelling IDs S27-C-flood, S27-C-setflood, S27-C-setfloodtimer, S27-C-setfloodmode, S27-C-clearflood. Behavior IDs S27-Bnn: B01 [not implemented; specified] Consecutive-message limit differs from per-user window → Different user breaks consecutive sequence but not another user window; B02 [partial; specified] Timer permits seconds → Validate count/window bounds; B03 [not implemented; specified] Normal/silent sanctions with temporary forms → Silent automated gate applies; B04 [not implemented; specified] Default exceeded-only deletion and clearflood whole observed sequence → Distinct exact ID sets, no unobserved history; B05 [partial; unresolved edge] Consecutive after-N versus timer more-than-N ambiguous → Record independent threshold decisions; B06 [partial; specified] Imported message-ID sorted-set member avoids same-timestamp collisions → Two messages at same mocked timestamp count separately; B07 [partial; proposed safety hardening] Redelivery/edits must not inflate counts (proposed hardening) → Same delivery counted once, changed edit reevaluates content.

S27-MODE-TOKEN IDs (kick ban tban mute tmute skick sban smute); Flood action form; phase7; implementation {partial: kick,ban,mute; not implemented: tban,tmute,skick,sban,smute}; acceptance: Correct sanction/deadline; automated silent owner/log gate and loud fallback respected

Variants: S27-V-clearflood-on-off [not implemented; specified] `/clearflood on|off` → Exact deletion IDs for each branch

**S28 AntiRaid — phase7; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/anti-spam/antiraid/

Commands /raidtime, /raidactiontime, /antiraid, /autoantiraid; spelling IDs S28-C-raidtime, S28-C-raidactiontime, S28-C-antiraid, S28-C-autoantiraid. Behavior IDs S28-Bnn: B01 [not implemented; specified] Active joins temporary banned with default6h activation/default1h ban → Independent deadlines and bounded ban; B02 [not implemented; specified] Antiraid status/button/on/custom duration/off → Off immediately stops new enforcement; B03 [not implemented; specified] Auto threshold more-than-N joins in under1minute → N versus N+1 and exact60s boundary; B04 [not implemented; specified] Approval/admin/federation exemptions open → No implicit exemption inferred.

Variants: S28-V-antiraid-variants [not implemented; specified] `/antiraid status|on|TIME|off` → Configured6h versus override, immediate off; S28-V-autoantiraid-off [not implemented; specified] `/autoantiraid off|no` → No automatic activation

**S29 Federation overview — phase9; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/federations/

Behavior IDs S29-Bnn: B01 [not implemented; specified] Federation owner/admin domain and opt-in groups → Fed authority distinct from Telegram group administration; B02 [not implemented; specified] Own bot namespace, no Rose private network/global bans → Foreign bot/fed IDs cannot grant authority; B03 [not implemented; specified] Keep existing optional CAS separate → CAS setting never substitutes for federation trust.

**S30 Federation info — phase9; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/federations/fedinfo/

Commands /fedinfo, /fedadmins, /chatfed, /myfeds; spelling IDs S30-C-fedinfo, S30-C-fedadmins, S30-C-chatfed, S30-C-myfeds. Behavior IDs S30-Bnn: B01 [not implemented; specified] Current/owned/explicit fed ID context → Group and PM resolve intended federation; B02 [not implemented; specified] Myfeds lists admin memberships with distinct IDs → No chat-ID conflation and no foreign namespace leak.

**S31 Creating federations — phase9; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/federations/creating/

Commands /newfed, /delfed, /renamefed; spelling IDs S31-C-newfed, S31-C-delfed, S31-C-renamefed. Behavior IDs S31-Bnn: B01 [not implemented; specified] PM-only create/delete with one owned federation per user → Group form rejected and concurrent second creation denied; B02 [not implemented; specified] Names64-character truncation and returned ID → Boundary and multicodepoint tests; B03 [not implemented; specified] Irreversible deletion removes fed data while Telegram bans persist → No mass unban during deletion; B04 [not implemented; specified] Rename separate from unsupported transfer → No transfer/title requirement inferred.

**S32 Managing federations — phase10; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/federations/managing/

Commands /fedpromote, /feddemote, /feddemoteme, /fedreason, /fednotif, /setfedlog, /unsetfedlog, /fbanlist, /importfbans, /subfed, /unsubfed, /fedsubs; spelling IDs S32-C-fedpromote, S32-C-feddemote, S32-C-feddemoteme, S32-C-fedreason, S32-C-fednotif, S32-C-setfedlog, S32-C-unsetfedlog, S32-C-fbanlist, S32-C-importfbans, S32-C-subfed, S32-C-unsubfed, S32-C-fedsubs. Behavior IDs S32-Bnn: B01 [not implemented; specified] Owner promote/demote and self-demote explicit ID → Local group admin cannot grant fed role; B02 [not implemented; specified] Required reason toggle → Missing required reason rejected; B03 [not implemented; specified] Owner PM notifications defaulton independent from logs → Turning off PM notification keeps log delivery; B04 [not implemented; specified] Channel fed-ID setup requires owner confirmation → Wrong owner/forged destination denied; B05 [not implemented; specified] Banlist csv/minicsv/json and once30minutes limit → Each format and 29m59s/30m boundary; B06 [not implemented; specified] Reply imports CSV id/reason or JSONL/NDJSON user_id optionalname/username/reason → Multiple newline objects parsed, malformed batch bounded; B07 [not implemented; specified] Directed subscriptions apply to linked groups → Direction/source provenance preserved and cycles policy explicit.

S32-EXPORT-TOKEN IDs (csv minicsv json); Federation banlist format; phase10; implementation {not implemented: csv,minicsv,json}; acceptance: Serialize actual fields; once30min limit applies

S32-IMPORT-TOKEN IDs (CSV JSONL NDJSON); Federation ban import format; phase10; implementation {not implemented: CSV,JSONL,NDJSON}; acceptance: CSV id/reason or newline user_id objects; optional name/username/reason and malformed records bounded

**S33 Joining federations — phase9; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/federations/joining/

Commands /joinfed, /leavefed, /quietfed; spelling IDs S33-C-joinfed, S33-C-leavefed, S33-C-quietfed. Behavior IDs S33-Bnn: B01 [not implemented; specified] Group creator alone joins/leaves without fed ownership → Creator can join another owner fed, ordinary admin cannot; B02 [not implemented; specified] Quietfed suppresses explanation while enforcing → Same ban with and without visible output.

**S34 Federation bans — phase10; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/federations/fedbans/

Commands /fban, /unfban; spelling IDs S34-C-fban, S34-C-unfban. Behavior IDs S34-Bnn: B01 [not implemented; specified] Group command authority is federation role, not Telegram admin → Fed admin member allowed, local admin without fed role denied; B02 [not implemented; specified] PM targets owned federation even when connected → Connection cannot redirect fed ban; B03 [not implemented; specified] Active enforce observed users silently across linked groups → No per-group visible/log fanout notification; B04 [not implemented; specified] Passive join/speak checks direct/subscribed bans explain source unless quiet → Source reason retained; B05 [not implemented; specified] Minimal observed membership, no unavailable history enumeration → Only known presence selected and bounded jobs proposed.

**S35 User federation commands — phase10; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/federations/user-commands/

Commands /fedstat, /fbanstat; spelling IDs S35-C-fedstat, S35-C-fbanstat. Behavior IDs S35-Bnn: B01 [not implemented; specified] All-user own/reply/target/target+fedID ban query → Return reason/date in intended namespace; B02 [not implemented; specified] Fbanstat ID own-query alias context → No target ambiguity or tenant leak.

Variants: S35-V-fedstat-target-fed [not implemented; specified] `/fedstat TARGET FED_ID` → No ID conflation, reason/date intended bot namespace

**S36 Filters — phase3; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/filters/

Commands /filter, /stop, /stopall, /filters; spelling IDs GG-CMD-filter, GG-CMD-stop, S36-C-stopall, GG-CMD-filters. Behavior IDs S36-Bnn: B01 [partial; specified] Words/quoted phrases/parenthesized multiple/media optionaltext → Each trigger and payload round-trips; B02 [not implemented; specified] Stopall creator-only → Ordinary admin denied; B03 [partial; specified] Default reply/fill trigger sender and replytag selects replied user → Different users produce intended fillings; B04 [not implemented; specified] Prefix and exact matcher → Start versus whole-message behavior distinct; B05 [not implemented; specified] User/admin/allow_bot modifiers and defaultignorebots → Each role branch and opt-in tested; B06 [not implemented; specified] Clone command optionaldescription publishes slash suggestion → Validate spelling and documented fewer-than32 against Telegram limit.

S36-MOD-TOKEN IDs (replytag user admin allow_bot command); Filter modifier; phase3; implementation {not implemented: replytag,user,admin,allow_bot,command}; acceptance: Assert specified role/filling/publishing effect and default behavior when absent

S36-MATCH-TOKEN IDs (prefix exact); Filter match mode; phase3; implementation {partial: prefix,exact}; acceptance: Prefix matches start only; exact entire message only

Variants: S36-V-filter-multimedia [partial; specified] `/filter word|"phrase"|(a,b) [replied media]` → Exact trigger parsing and media payload roundtrip

**S37 Notes — phase3; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/notes/

Commands /save, /get, /notes, /clear, /privatenotes; spelling IDs GG-CMD-save, GG-CMD-get, GG-CMD-notes, GG-CMD-clear, S37-C-privatenotes. Behavior IDs S37-Bnn: B01 [partial; specified] Save replaces text/replied attachment with quoted name → Same name replaces correct bot/chat record; B02 [partial; specified] Hashtag and get open note → Explicit retrieval forms resolve same content; B03 [partial; specified] Notes public by default unless admin modifier → Member reads public but not admin note; B04 [not implemented; specified] Privatenotes PM button with private/noprivate overrides → Per-note group override wins; B05 [partial; specified] Fill replied user otherwise opener → No accidental sender substitution; B06 [not implemented; unresolved edge] Clone repeated time versus repeat time spelling conflict → Proposed alias pair tested only after decision; B07 [not implemented; specified] Repeated notes actual durable delivery (clone contract) → Restart/retry preserves bounded schedule, not selector stub.

S37-MOD-TOKEN IDs (admin private noprivate repeat repeated); Note modifier; phase3; implementation {not implemented: admin,private,noprivate,repeat,repeated}; acceptance: Assert read/delivery effect; repeat/repeated proposed alias pair remains unresolved pending decision

Variants: S37-V-hash-note [partial; specified] `#note` → Same content as get, same auth; S37-V-quoted-name [not implemented; specified] `/save "note name" ...` → Replace/retrieve exact stored name; S37-V-repeat-duration [not implemented; unresolved source defect] `{repeat TIME}|{repeated TIME}` → Proposed aliases, decision and durable schedule tests before implementation

**S38 Formatting — phase3; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/formatting/

Behavior IDs S38-Bnn: B01 [partial; specified] Existing HTML stored/rendered as legacy HTML → No Markdown reinterpretation or destructive data migration; B02 [not implemented; specified] Ordinary/expandable quotations separate → Correct Telegram entities for both; B03 [not implemented; specified] URL buttons, same-row and #note menu targets → Correct target kind and rows; B04 [partial; specified] Username filling fallback → Absent username still gives safe rendered text; B05 [not implemented; specified] Control modifiers removed from visible content → Flags sent to Telegram and text safe; B06 [not implemented; specified] Random alternatives use %%% → Select valid alternative without exposing delimiter; B07 [not implemented; specified] Protect Telegram flag is not capture guarantee → Truthful user-facing help.

S38-STYLE-TOKEN IDs (code italic bold strike underline spoiler quote expandable-quote hyperlink); Formatting style; phase3; implementation {not implemented: code,italic,bold,strike,underline,spoiler,quote,expandable-quote,hyperlink}; acceptance: Correct Telegram entities and escaped Unicode render; legacy HTML preserved

S38-FILL-TOKEN IDs (first last fullname username mention id chatname rules); Shared filling; phase3; implementation {partial: first,username,mention,id; not implemented: last,fullname,chatname,rules}; acceptance: Use intended event user/chat; missing fields fallback safely; rules yields correct button

S38-CONTROL-TOKEN IDs (preview nonotif protect mediaspoiler); Content control; phase3; implementation {not implemented: preview,nonotif,protect,mediaspoiler}; acceptance: Telegram flag changes and token not displayed as literal text

S38-BUTTON-TOKEN IDs (buttonurl same note); Button syntax; phase3; implementation {not implemented: buttonurl,same,note}; acceptance: URL destination, same row, #note menu target independently rendered

Variants: S38-V-random [not implemented; specified] `%%%` → Delimiter not visible and one valid alternative selected

**S39 Button generator — phase3; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/formatting/button-generator/

Behavior IDs S39-Bnn: B01 [not implemented; specified] Equivalent button-markup helper label/link/row layout → Editor builds working URL/note buttons with no copied site assets.

**S40 Connections — phase8; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/connections/

Commands /connect, /disconnect, /connection, /reconnect; spelling IDs S40-C-connect, S40-C-disconnect, S40-C-connection, S40-C-reconnect. Behavior IDs S40-Bnn: B01 [not implemented; specified] Any chat member connects with precise rights required to mutate → Member can read connection but settings denied; B02 [not implemented; specified] PM connect ID/@group and group personal button → Correct chat selected without exposing another user session; B03 [not implemented; specified] One active group replaces previous → Switch atomically updates selected target; B04 [not implemented; specified] PM connect noargs lastfive and reconnect switching → Sixth distinct connection evicts oldest history entry; B05 [not implemented; specified] Context id and disconnect → ID matches active chat and disconnect clears active context; B06 [not implemented; specified] History never authorizes, revalidate membership/rights → Removed member and demoted admin denied on reuse.

Variants: S40-V-connect-id-group [not implemented; specified] `/connect ID|@group (PM)` → Member validated and active chat replaced; S40-V-connect-lastfive [not implemented; specified] `/connect (PM noargs)` → Sixth chat evicts oldest; history not authorization

**S41 Echo and broadcast — phase8; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/echo/

Commands /echo, /say, /broadcast; spelling IDs S41-C-echo, S41-C-say, S41-C-broadcast. Behavior IDs S41-Bnn: B01 [not implemented; specified] Echo/say formatted resend aliases → Both produce same payload semantics; B02 [not implemented; specified] Broadcast belongs to bot owner groups → Arbitrary group admin cannot send to all shared-bot groups; B03 [not implemented; specified] Standalone operator/factory owner destination isolation → Child owner cannot address sibling/standalone destinations; B04 [not implemented; specified] Rate-limited bounded fanout → Backpressure and failure outcomes explicit.

**S42 Settings exports/imports/reset — phase11; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/exports/

Commands /export, /import, /reset; spelling IDs S42-C-export, S42-C-import, S42-C-reset. Behavior IDs S42-Bnn: B01 [not implemented; specified] Admin export JSON with optionalmodule selection → Selected modules only, omit secrets; B02 [not implemented; specified] Creator reply import all/selected → No cross-bot/chat data overwrite; B03 [not implemented; specified] Creator reset requires confirmation → Wrong user/chat/expired confirmation denied; B04 [not implemented; unresolved edge] Rate-limited operations exact interval unspecified → Require policy rather than invented limit; B05 [not implemented; unresolved edge] Full Rose schema unknown and ownformat roundtrip required → Reject claimed Rose compatibility without verified format.

Variants: S42-V-select-modules [not implemented; specified] `/export MODULES; /import MODULES` → Only selected known modules roundtrip

**S43 Privacy — phase11; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/privacy/

Commands /privacy; spelling IDs S43-C-privacy. Behavior IDs S43-Bnn: B01 [not implemented; specified] PM-only policy/access/deletion of personal data → Group call directs private and wrong user cannot access record; B02 [not implemented; unresolved edge] Fields and retention periods unspecified policy → No automatic7/30/90-day purge or blanket deletion assumption.

**S44 Topics — phase8; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/topics/

Commands /setactiontopic, /actiontopic, /newtopic, /renametopic, /closetopic, /reopentopic, /deletetopic; spelling IDs S44-C-setactiontopic, S44-C-actiontopic, S44-C-newtopic, S44-C-renametopic, S44-C-closetopic, S44-C-reopentopic, S44-C-deletetopic. Behavior IDs S44-Bnn: B01 [not implemented; specified] Settings shared across forum topics → One topic change visible in another; B02 [not implemented; specified] Welcomes general/default actiontopic then currenttopic selection → Deleted/missing/general topic handled explicitly; B03 [not implemented; specified] Topic management requires manage_topics → Unrelated admin right denied; B04 [not implemented; specified] Delete topic removes topic/messages → Explicit destructive confirmation proposal; B05 [not implemented; specified] Closed topic still permits Telegram admins posting → No incorrect no-post guarantee.

**S45 Command cleaning — phase8; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/cleaning/clean-command/

Commands /cleancommand, /keepcommand, /cleancommandtypes; spelling IDs S45-C-cleancommand, S45-C-keepcommand, S45-C-cleancommandtypes. Behavior IDs S45-Bnn: B01 [not implemented; specified] Command cleaning runs after authorized handling for any sender → Execution occurs before deletion; B02 [not implemented; unresolved edge] Other includes unknown/otherbot commands → No conflation with disable or lock; B03 [not implemented; unresolved edge] Source example join/leave/pin conflicts with table → Use all/admin/user/other canonical proposal with tests.

S45-CLEAN-TOKEN IDs (all admin user other); Command-clean category; phase8; implementation {not implemented: all,admin,user,other}; acceptance: Authorized command executes before delete; unknown/otherbot matches other

Variants: S45-V-table-typo [not implemented; unresolved source defect] `join/leave/pin example` → Canonical table proposed; typo recorded

**S46 Bot-message cleaning — phase8; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/cleaning/clean-message/

Commands /cleanmsg, /keepmsg, /cleanmsgtypes; spelling IDs S46-C-cleanmsg, S46-C-keepmsg, S46-C-cleanmsgtypes. Behavior IDs S46-Bnn: B01 [not implemented; specified] Configured bot message categories removed after5minutes → Only selected action/filter/note IDs deleted; B02 [not implemented; specified] Timed botclean separate from silence and serviceclean → No immediate deletion or wrong message class.

S46-CLEAN-TOKEN IDs (all action filter note); Bot-message-clean category; phase8; implementation {not implemented: all,action,filter,note}; acceptance: Only category messages deleted after5min, timer survives restart when implemented

**S47 Service-message cleaning — phase8; spec specified except explicit questions/defects; implementation partial.** https://missrose.org/docs/cleaning/clean-service/

Commands /cleanservice, /nocleanservice, /cleanservicetypes; spelling IDs S47-C-cleanservice, S47-C-nocleanservice, S47-C-cleanservicetypes. Behavior IDs S47-Bnn: B01 [partial; specified] Boolean/all or selected service categories → Only selected service messages deleted; B02 [partial; specified] Other payment/proximity/webapp/autodelete still processed → Payment handler runs before cleanup; B03 [partial; specified] Telegram may omit join/leave in large groups → No false claim cleanup executed; B04 [partial; specified] Undeletable service/age API limits → Failure produces truthful outcome.

S47-CLEAN-TOKEN IDs (join leave other photo pin title videochat); Service-clean category; phase8; implementation {partial: join,leave; not implemented: other,photo,pin,title,videochat}; acceptance: Only category deleted; payment/function processing still runs and API limits honored

Variants: S47-V-boolean-service [not implemented; specified] `/cleanservice BOOL|all|TYPES` → Map intended categories without payment bypass

**S48 Advanced overview — phase0; spec specified except explicit questions/defects; implementation not applicable.** https://missrose.org/docs/advanced/

Behavior IDs S48-Bnn: B01 [not applicable; specified] Advanced navigation only → Cover S49/S50 without duplicate commands.

**S49 Automated silent actions — phase8; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/advanced/silent-actions/

Commands /silentactions; spelling IDs S49-C-silentactions. Behavior IDs S49-Bnn: B01 [not implemented; specified] Automated silent enable is creator-only with logchannel → Nonowner or missing log destination denied; B02 [not implemented; specified] Enable does not convert existing settings → Each automatic silent action explicitly selected; B03 [not implemented; specified] Disable or log removal makes configured silent actions loud → Next automatic event emits visible feedback; B04 [not implemented; specified] Temporary silent actions retain durations → Invalid duration cannot become permanent; B05 [not implemented; specified] Manual silent commands separate and ungated by this setting → Manual contract follows S14 only.

S49-SILENT-TOKEN IDs (sban skick smute swarn); Automated silent action; phase8; implementation {not implemented: sban,skick,smute,swarn}; acceptance: Creator enables with log; explicit selection; missing log/disabled becomes loud; temporary durations retained

**S50 Bot-to-bot — phase8; spec specified except explicit questions/defects; implementation not implemented.** https://missrose.org/docs/advanced/bot-to-bot/

Commands /bot2bot, /bot2botskipreview; spelling IDs S50-C-bot2bot, S50-C-bot2botskipreview. Behavior IDs S50-Bnn: B01 [not implemented; specified] Modes off(default)/admin/all retain actual command rights → Nonadmin bot never gains admin rights; B02 [not implemented; specified] Bot-admin mutations need human review by default → Denied without attributable authorized reviewer; B03 [not implemented; specified] Skipreview bypass still checks bot rights → Missing Telegram right still denied; B04 [not implemented; specified] Filter allow_bot optin and deploymentBotFather requirement → Defaultignore and optin/deployment prerequisites distinct; B05 [not implemented; proposed safety hardening] Selftrigger loops and replayed reviews defended (hardening) → Bot output cannot cause unbounded execution or reuse approved review; B06 [not implemented; specified] Bot sender never implies owner → Owner-only command denied.

S50-BOTMODE-TOKEN IDs (off admin all); Bot-to-bot mode; phase8; implementation {not implemented: off,admin,all}; acceptance: Off default; admin/all still require precise rights and human review for mutations by default

**T01 Telegram capability notes — phase1; spec specified except explicit questions/defects; implementation SDK inspected; deployment unverified.** https://core.telegram.org/bots/api

Behavior IDs T01-Bnn: B01 [SDK inspected; deployment unverified; specified] Installed SDK reaction deletion methods and return_bots exist → Introspect SDK independently from deployment support; B02 [SDK inspected; deployment unverified; specified] Reaction removals require delete right → Deny missing caller/bot capability; B03 [SDK inspected; deployment unverified; specified] Reaction subscriptions/admin eligibility explicit → Runtime allowed_updates includes required types when implemented; B04 [SDK inspected; deployment unverified; specified] Guest/bot messages and reaction permission supported in schema → Classify without inferred human owner; B05 [SDK inspected; deployment unverified; specified] Nonadmin getChatMember guarantees restricted → Failure cannot authorize; B06 [SDK inspected; deployment unverified; specified] Bulk deletion max100 with no per-ID success count → Report submitted/acknowledged only; B07 [SDK inspected; deployment unverified; specified] Restriction veryshort/long can become permanent → Reject unsafe deadlines; B08 [SDK inspected; deployment unverified; specified] Joinrequest short user_chat_id contactwindow → Deadline expiry fails safely; B09 [SDK inspected; deployment unverified; unresolved edge] Deployed API version unobserved → Keep deployment validation open, no mutabletag version claim.
