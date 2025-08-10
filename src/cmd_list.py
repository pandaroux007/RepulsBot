class CmdList:
    VIDEOSTATES = "video_leaderboard"
    PING = "ping"
    AVATAR = "avatar"
    MEMBERCOUNT = "member_count"
    ESPORTSTATES = "esports_roadmap"
    CLOSETICKET = "close_ticket"
    SETUPTICKET = "setup_ticket"
    PURGE = "purge"
    HELP = "help"
    ABOUTMEMBER = "about_member"
    ABOUTSERVER = "about_server"
    ABOUTGAME = "about_game"
    WIKI = "wiki"
    SERVERFAQ = "server_faq"
    GAMEFAQ = "game_faq"

ADMIN_SLASH_COMMANDS = {
    CmdList.PURGE,
    CmdList.CLOSETICKET
}

ADMIN_CTX_COMMANDS = {
    CmdList.SETUPTICKET
}