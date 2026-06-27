
-- Configuration --------------------------------------
AUTOTRACKER_ENABLE_DEBUG_LOGGING = true and ENABLE_DEBUG_LOG
AUTOTRACKER_ENABLE_DEBUG_LOGGING_AP = true and AUTOTRACKER_ENABLE_DEBUG_LOGGING
-------------------------------------------------------
ScriptHost:LoadScript("scripts/settings.lua")
-- loads the AP autotracking code
ScriptHost:LoadScript("scripts/autotracking/archipelago.lua")
