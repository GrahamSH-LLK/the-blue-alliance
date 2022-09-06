import datetime
import json
from typing import Optional

from flask import abort, redirect, request, url_for
from google.appengine.ext import ndb
from pyre_extensions import none_throws
from werkzeug.wrappers import Response

from backend.common.consts.comp_level import COMP_LEVELS, COMP_LEVELS_VERBOSE_FULL
from backend.common.consts.event_type import EventType, TYPE_NAMES as EVENT_TYPE_NAMES
from backend.common.consts.playoff_type import (
    PlayoffType,
    TYPE_NAMES as PLAYOFF_TYPE_NAMES,
)
from backend.common.helpers.match_helper import MatchHelper
from backend.common.helpers.playoff_advancement_helper import PlayoffAdvancementHelper
from backend.common.helpers.season_helper import SeasonHelper
from backend.common.helpers.website_helper import WebsiteHelper
from backend.common.manipulators.event_details_manipulator import (
    EventDetailsManipulator,
)
from backend.common.manipulators.event_manipulator import EventManipulator
from backend.common.manipulators.event_team_manipulator import EventTeamManipulator
from backend.common.manipulators.match_manipulator import MatchManipulator
from backend.common.models.api_auth_access import ApiAuthAccess
from backend.common.models.district import District
from backend.common.models.event import Event
from backend.common.models.event_details import EventDetails
from backend.common.models.event_team import EventTeam
from backend.common.models.keys import EventKey, Year
from backend.common.models.match import Match
from backend.common.models.media import Media
from backend.common.sitevars.cmp_registration_hacks import ChampsRegistrationHacks
from backend.web.profiled_render import render_template


def event_list(year: Optional[Year]) -> str:
    if year is None:
        year = datetime.datetime.now().year

    events = Event.query(Event.year == year).order(Event.start_date).fetch(10000)

    template_values = {
        "valid_years": SeasonHelper.get_valid_years(),
        "selected_year": year,
        "events": events,
    }

    return render_template("admin/event_list.html", template_values)


def event_detail(event_key: EventKey) -> str:
    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)
    event.prep_awards_matches_teams()

    reg_sitevar = ChampsRegistrationHacks.get()
    api_keys = ApiAuthAccess.query(
        ApiAuthAccess.event_list == ndb.Key(Event, event_key)
    ).fetch()
    event_medias = Media.query(Media.references == event.key).fetch(500)
    playoff_template = PlayoffAdvancementHelper.playoff_template(event)
    elim_bracket_html = render_template(
        "bracket_partials/bracket_table.html",
        {"bracket_table": event.playoff_bracket, "event": event},
    )
    advancement_html = (
        render_template(
            "playoff_partials/{}.html".format(playoff_template),
            {
                "event": event,
                "playoff_advancement": event.playoff_advancement,
                "playoff_advancement_tiebreakers": PlayoffAdvancementHelper.ROUND_ROBIN_TIEBREAKERS.get(
                    event.year
                ),
                "bracket_table": event.playoff_bracket,
            },
        )
        if playoff_template
        else "None"
    )

    _, organized_matches = MatchHelper.organized_matches(event.matches)
    match_stats = []
    for comp_level in COMP_LEVELS:
        level_matches = organized_matches[comp_level]
        if not level_matches:
            continue
        match_stats.append(
            {
                "comp_level": comp_level,
                "level_name": COMP_LEVELS_VERBOSE_FULL[comp_level],
                "total": len(level_matches),
                "played": len(list(filter(lambda m: m.has_been_played, level_matches))),
                "unplayed": len(
                    list(filter(lambda m: not m.has_been_played, level_matches))
                ),
            }
        )

    template_values = {
        "event": event,
        "medias": event_medias,
        "flushed": request.args.get("flushed"),
        "playoff_types": PLAYOFF_TYPE_NAMES,
        "write_auths": api_keys,
        "event_sync_disable": event_key in reg_sitevar["divisions_to_skip"],
        "set_start_day_to_last": event_key in reg_sitevar["set_start_to_last_day"],
        "skip_eventteams": event_key in reg_sitevar["skip_eventteams"],
        "event_name_override": next(
            iter(
                filter(
                    lambda e: e.get("event") == event_key,
                    reg_sitevar["event_name_override"],
                )
            ),
            {},
        ).get("name", ""),
        "elim_bracket_html": elim_bracket_html,
        "advancement_html": advancement_html,
        "match_stats": match_stats,
        "deleted_count": request.args.get("deleted"),
    }

    return render_template("admin/event_details.html", template_values)


def event_edit(event_key: EventKey) -> Response:
    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    template_values = {
        "event": event,
        "alliance_selections": json.dumps(event.alliance_selections),
        "rankings": json.dumps(event.rankings),
        "playoff_types": PLAYOFF_TYPE_NAMES,
        "event_types": EVENT_TYPE_NAMES,
    }
    return render_template("admin/event_edit.html", template_values)


def event_delete(event_key: EventKey) -> Response:
    if request.method == "POST":
        if not Event.validate_key_name(event_key):
            abort(404)

        event = Event.get_by_id(event_key)
        if not event:
            abort(404)

        matches = Match.query(Match.event == event.key).fetch(5000)
        MatchManipulator.delete(matches)

        event_teams = EventTeam.query(EventTeam.event == event.key).fetch(5000)
        EventTeamManipulator.delete(event_teams)

        EventManipulator.delete(event)

        return redirect(url_for("admin.event_list"))
    else:
        if not Event.validate_key_name(event_key):
            abort(404)

        event = Event.get_by_id(event_key)
        if not event:
            abort(404)

        template_values = {"event": event}
        return render_template("admin/event_delete.html", template_values)


def event_create() -> Response:
    template_values = {
        "event_types": EVENT_TYPE_NAMES,
    }

    # POSTs to /admin/event/edit
    return render_template("admin/event_create.html", template_values)


def event_edit_post(event_key: Optional[EventKey] = None) -> Response:
    # Note, we don't actually use event_key.

    start_date = None
    if request.form.get("start_date"):
        start_date = datetime.datetime.strptime(
            request.form.get("start_date"), "%Y-%m-%d"
        )

    end_date = None
    if request.form.get("end_date"):
        end_date = datetime.datetime.strptime(request.form.get("end_date"), "%Y-%m-%d")

    first_code = request.form.get("first_code", None)
    district_key = request.form.get("event_district_key", None)
    parent_key = request.form.get("parent_event", None)

    division_key_names = json.loads(request.form.get("divisions", "[]"))
    division_keys = (
        [ndb.Key(Event, key) for key in division_key_names]
        if division_key_names
        else []
    )

    website = WebsiteHelper.format_url(request.form.get("website"))

    key = str(request.form.get("year")) + str.lower(
        str(request.form.get("event_short"))
    )
    if event_key is not None and event_key != key:
        abort(400)

    event = Event(
        id=key,
        end_date=end_date,
        event_short=request.form.get("event_short"),
        first_code=first_code if first_code and first_code != "None" else None,
        event_type_enum=int(request.form.get("event_type", EventType.UNLABLED)),
        district_key=ndb.Key(District, request.form.get("event_district_key"))
        if district_key and district_key != "None"
        else None,
        venue=request.form.get("venue"),
        venue_address=request.form.get("venue_address"),
        city=request.form.get("city"),
        state_prov=request.form.get("state_prov"),
        postalcode=request.form.get("postalcode"),
        country=request.form.get("country"),
        name=request.form.get("name"),
        short_name=request.form.get("short_name"),
        start_date=start_date,
        website=website,
        first_eid=request.form.get("first_eid"),
        year=int(none_throws(request.form.get("year"))),
        official={"true": True, "false": False}.get(
            request.form.get("official", "false").lower()
        ),
        enable_predictions={"true": True, "false": False}.get(
            request.form.get("enable_predictions", "false").lower()
        ),
        facebook_eid=request.form.get("facebook_eid"),
        custom_hashtag=request.form.get("custom_hashtag"),
        webcast_json=request.form.get("webcast_json"),
        playoff_type=int(request.form.get("playoff_type", PlayoffType.BRACKET_8_TEAM)),
        parent_event=ndb.Key(Event, parent_key)
        if parent_key and parent_key.lower() != "none"
        else None,
        divisions=division_keys,
    )
    event = EventManipulator.createOrUpdate(event)

    if request.form.get("alliance_selections_json") or request.form.get(
        "rankings_json"
    ):
        event_details = EventDetails(
            id=event_key,
            alliance_selections=json.loads(
                request.form.get("alliance_selections_json", "[]")
            ),
            rankings=json.loads(request.form.get("rankings_json", "[]")),
        )
        EventDetailsManipulator.createOrUpdate(event_details)

    # TODO port this?
    # MemcacheWebcastFlusher.flushEvent(event.key_name)

    return redirect(url_for("admin.event_detail", event_key=event.key_name))


def event_detail_post(event_key: EventKey) -> Response:
    if not Event.validate_key_name(event_key):
        abort(404)

    event = Event.get_by_id(event_key)
    if not event:
        abort(404)

    reg_sitevar = ChampsRegistrationHacks.get()
    new_divisions_to_skip = reg_sitevar["divisions_to_skip"]
    if request.form.get("event_sync_disable"):
        if event_key not in new_divisions_to_skip:
            new_divisions_to_skip.append(event_key)
    else:
        new_divisions_to_skip = list(
            filter(lambda e: e != event_key, new_divisions_to_skip)
        )
    new_start_day_to_last = reg_sitevar["set_start_to_last_day"]
    if request.form.get("set_start_day_to_last"):
        if event_key not in new_start_day_to_last:
            new_start_day_to_last.append(event_key)
    else:
        new_start_day_to_last = list(
            filter(lambda e: e != event_key, new_start_day_to_last)
        )
    new_skip_eventteams = reg_sitevar["skip_eventteams"]
    if request.form.get("skip_eventteams"):
        if event_key not in new_skip_eventteams:
            new_skip_eventteams.append(event_key)
    else:
        new_skip_eventteams = list(
            filter(lambda e: e != event_key, new_skip_eventteams)
        )
    new_name_overrides = reg_sitevar["event_name_override"]
    form_name_override = request.form.get("event_name_override")
    if form_name_override:
        if not any(o["event"] == event_key for o in new_name_overrides):
            new_name_overrides.append(
                {
                    "event": event_key,
                    "name": form_name_override,
                    "short_name": form_name_override,
                }
            )
    else:
        new_name_overrides = list(
            filter(lambda o: o["event"] != event_key, new_name_overrides)
        )
    ChampsRegistrationHacks.put(
        {
            "divisions_to_skip": new_divisions_to_skip,
            "set_start_to_last_day": new_start_day_to_last,
            "skip_eventteams": new_skip_eventteams,
            "event_name_override": new_name_overrides,
        }
    )
    return redirect(url_for("admin.event_detail", event_key=event_key))