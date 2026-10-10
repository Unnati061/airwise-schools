"""Labelled synthetic week: ordinary lessons and one Monday outdoor activity."""
import json
from pathlib import Path

from .repair_contracts import RepairInput


def synthetic_week() -> RepairInput:
    school = json.loads(Path(__file__).with_name("data").joinpath("school.json").read_text())
    periods = [{"id": f"{day}-{p}", "day": day, "number": p}
               for day in ("Mon", "Tue", "Wed", "Thu", "Fri") for p in range(1, 9)]
    slots = [p["id"] for p in periods]
    teachers = [{"id": f"teacher-{s['id']}", "available_period_ids": slots,
                 "supervised_kinds": ["lesson", "pe", "indoor-movement"]} for s in school["sections"]]
    rooms = [{"id": f"room-{s['id']}", "kind": "classroom", "capacity": s["size"],
              "available_period_ids": slots} for s in school["sections"]]
    rooms.append({"id": "field", "kind": "outdoor", "capacity": 40, "available_period_ids": slots})
    activities = []
    for s in school["sections"]:
        for p in periods:
            activities.append({"id": f"{s['id']}:{p['id']}", "section_id": s["id"],
                               "teacher_id": f"teacher-{s['id']}", "label": "Synthetic classroom lesson",
                               "kind": "lesson", "duration_minutes": 40, "room_types": ["classroom"],
                               "original_period_id": p["id"], "original_room_id": f"room-{s['id']}",
                               "permitted_period_ids": [q["id"] for q in periods if q["day"] == p["day"]],
                               "permitted_room_ids": [f"room-{s['id']}"],
                               "fixed": p["number"] == 1})
    outdoor = next(a for a in activities if a["id"] == "6-a:Mon-2")
    outdoor.update(label="Synthetic PE", kind="pe", room_types=["outdoor"],
                   original_room_id="field", permitted_room_ids=["field"],
                   approved_alternatives=[{"id": "indoor-movement", "label": "Approved classroom movement",
                                           "kind": "indoor-movement", "room_types": ["classroom"],
                                           "room_ids": ["room-6-a"]}])
    return RepairInput(mode="SYNTHETIC", school_id=school["id"],
                       versions={"school": "synthetic-v1", "timetable": "synthetic-week-v1",
                                 "restrictions": "admin-confirmed-synthetic-v1"},
                       affected_day="Mon", sections=school["sections"], periods=periods,
                       teachers=teachers, rooms=rooms, activities=activities,
                       restrictions=[{"id": "synthetic-mon-outdoor", "kind": "outdoor_prohibited",
                                      "period_ids": [f"Mon-{p}" for p in range(1, 9)],
                                      "section_ids": [s["id"] for s in school["sections"]],
                                      "administrator_confirmed": True, "confirmed_by": "synthetic-administrator"}])


def shared_resources_week() -> RepairInput:
    """Sample: two PE lessons share a teacher; indoor rooms open later in the day."""
    data = synthetic_week().model_dump()
    data['versions']['timetable'] = 'sample-shared-resources-v1'
    data['versions']['restrictions'] = 'sample-shared-resources-v1'
    slots = [p['id'] for p in data['periods']]
    data['rooms'] += [
        {'id': 'field-annex', 'kind': 'outdoor', 'capacity': 40, 'available_period_ids': slots},
        {'id': 'movement-hall', 'kind': 'classroom', 'capacity': 40, 'available_period_ids': ['Mon-3', 'Mon-4']},
        {'id': 'movement-studio', 'kind': 'classroom', 'capacity': 40, 'available_period_ids': ['Mon-3', 'Mon-4']},
    ]
    data['teachers'].append({'id': 'teacher-cover', 'available_period_ids': slots, 'supervised_kinds': ['lesson']})
    activities = {a['id']: a for a in data['activities']}
    first = activities['6-a:Mon-2']
    first.update(label='PE / movement', permitted_period_ids=['Mon-2', 'Mon-3', 'Mon-4'])
    first['approved_alternatives'][0].update(room_ids=['movement-hall', 'movement-studio'])
    second = activities['6-b:Mon-3']
    second.update(label='PE / movement', kind='pe', teacher_id='teacher-6-a',
                  room_types=['outdoor'], original_room_id='field-annex',
                  permitted_period_ids=['Mon-3'], permitted_room_ids=['field-annex'],
                  approved_alternatives=[{'id': 'indoor-movement', 'label': 'Approved classroom movement',
                                          'kind': 'indoor-movement', 'room_types': ['classroom'],
                                          'room_ids': ['movement-hall']}])
    activities['6-a:Mon-3']['teacher_id'] = 'teacher-cover'
    for activity_id in ['6-a:Mon-3', '6-a:Mon-4']:
        activities[activity_id]['permitted_period_ids'] = ['Mon-2', activities[activity_id]['original_period_id']]
    fixed = activities['7-a:Mon-4']
    fixed.update(label='Fixed group lesson', original_room_id='movement-hall',
                 permitted_room_ids=['movement-hall'], fixed=True)
    data['restrictions'] = [{'id': 'sample-shared-indoor', 'kind': 'outdoor_prohibited',
                            'period_ids': ['Mon-2', 'Mon-3', 'Mon-4'], 'section_ids': ['6-a', '6-b'],
                            'administrator_confirmed': True, 'confirmed_by': 'sample-administrator'}]
    return RepairInput.model_validate(data)
