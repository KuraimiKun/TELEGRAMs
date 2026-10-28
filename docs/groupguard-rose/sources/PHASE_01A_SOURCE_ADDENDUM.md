# Phase 1A source and decision addendum

Checked by the reviewer on 12 October 2026, Asia/Jakarta. This supplements the condensed digest; it is not a full website archive. The cloud agent may cite it as reviewer-supplied evidence and must not claim direct retrieval.

## S17: self-kick purpose

Rose's disabling example expressly describes stopping users from kicking themselves with `/disable kickme`. Therefore the basic purpose of `/kickme` is established. Its eventual implementation must act on the invoking user, never accept an arbitrary other target. Optional arguments, exact error text and unusual edge behavior remain unspecified. `runs`, `saved`, and any uncertain `antiflood` alias meaning require separate evidence or an explicit unresolved entry. [Official disabling page](https://missrose.org/docs/moderation/disabling/).

## S09: permissions and anonymous verification

Settings use change-info; deletion uses delete-messages; sanctions use restrict-members; pinning, promotion and topic operations use their corresponding rights. The default anonymous flow asks for button verification and checks the human's actual permissions. Optional assumed anonymous admin permissions exclude owner authority. Our execution-time checks and immutable one-use approvals are implementation hardening choices. [Official administrator documentation](https://missrose.org/docs/moderation/admins/).

## T01: temporary deadlines and deletion evidence

The API treats ban/restriction deadlines under 30 seconds or over 366 days from its current time as permanent. Bulk deletion accepts 1–100 IDs, skips missing messages and returns a Boolean, not a per-message result list. Membership lookup for other users is guaranteed only when the bot is a chat administrator. [Official Bot API](https://core.telegram.org/bots/api).

The 60-second through 365-day input interval in this handoff is a deliberate local safety margin. Form a new command's deadline immediately before dispatch, after authorization. Recheck an existing absolute deadline with a positive margin inside the API's permanent-conversion boundaries; reject unsafe or expired deadlines instead of submitting them. Account for integer timestamps so a valid one-minute input still works. This cannot prove an arbitrary network delay is impossible, so document that practical limit. No general-purpose timer bounds are changed by this decision.

## S32: phase assignment

Keep federation role management, reason policy, owner notifications and log configuration in Phase 9. Keep ban-list export/import and directed subscriptions in Phase 10. This is a sequencing correction, not a new feature or a removal. [Official federation management page](https://missrose.org/docs/federations/managing/).
