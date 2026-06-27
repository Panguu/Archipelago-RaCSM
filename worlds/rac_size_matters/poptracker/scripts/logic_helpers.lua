function has_projectile_weapon()
  return has("lacerator") or has("concussion_gun") or has("shock_rocket") or has("sniper_mine") or has("scorcher") or has("laser_tracer") or has("suck_cannon") or has("ryno")
end

-- Combo helpers, one per repeated gadget/weapon requirement used across
-- multiple locations/regions (mirrors worlds/rac_size_matters/rules/*.py).

function kalidon_inside()
  return has("hypershot") and has("shrink_ray")
end

function ryllus_full()
  return has("hypershot") and has("sprout_o_matic")
end

function metalis_door()
  return has("polarizer") and has("hypershot")
end

function dreamtime_base()
  return has("hypershot") and has("sprout_o_matic")
end

function dreamtime_crab()
  return dreamtime_base() and has_projectile_weapon()
end

function outpost_omega_facility()
  return has("shrink_ray") and has("hypershot") and has("sprout_o_matic")
end

function challax_base()
  return has("shrink_ray") and has("polarizer")
end

function challax_sprout()
  return challax_base() and has("sprout_o_matic")
end

function challax_helmet()
  return challax_sprout() or has("dayni_moon")
end

function dayni_moon_base()
  return has("sprout_o_matic") and has_projectile_weapon()
end

function dayni_moon_shrink()
  return dayni_moon_base() and has("shrink_ray")
end

function quodrona_checks()
  return has("shrink_ray") and has("hypershot")
end

function inside_clank_entrance()
  return has("dayni_moon") and has("sprout_o_matic") and has("shrink_ray")
    and has("hypershot") and has("polarizer") and has_projectile_weapon()
end
