"""DRF serializers for BMKG earthquake API responses.

Organised with shared base classes to eliminate field duplication
across M5 / Felt / Tsunami / Latest alert envelopes and Mon3 / Yr5
GeoJSON catalogs.
"""

from __future__ import annotations

from rest_framework import serializers


# ── Custom fields ────────────────────────────────────────────


class IndonesianBooleanField(serializers.BooleanField):
    """Accepts ``'Ya'`` / ``'Tidak'`` (case-insensitive) as booleans."""

    TRUE_VALUES = serializers.BooleanField.TRUE_VALUES | {"ya"}
    FALSE_VALUES = serializers.BooleanField.FALSE_VALUES | {"tidak"}


# ── Shared geometry ─────────────────────────────────────────


class GeoPointSerializer(serializers.Serializer):
    """GeoJSON ``Point`` geometry — reused across all GeoJSON endpoints."""

    type = serializers.CharField()
    coordinates = serializers.ListField(child=serializers.FloatField())


class AlertPointSerializer(serializers.Serializer):
    """CAP coordinate string ``"lon,lat"``."""

    coordinates = serializers.CharField()


# ── Shared alert envelope / info ─────────────────────────────


class BaseAlertEnvelopeSerializer(serializers.Serializer):
    """Common CAP alert envelope fields."""

    identifier = serializers.CharField()
    sender = serializers.CharField()
    sent = serializers.CharField()
    status = serializers.CharField()
    msgType = serializers.CharField()
    scope = serializers.CharField()
    code = serializers.CharField()


class BaseAlertInfoSerializer(serializers.Serializer):
    """Fields shared by M5 / Felt / Latest / Tsunami ``<info>`` blocks."""

    event = serializers.CharField()
    date = serializers.DateField(input_formats=["%d-%m-%y", "%d-%m-%Y"])
    time = serializers.CharField()
    point = AlertPointSerializer()
    latitude = serializers.CharField()
    longitude = serializers.CharField()
    magnitude = serializers.FloatField(allow_null=True, required=False)
    depth = serializers.CharField()
    area = serializers.CharField()
    eventid = serializers.IntegerField()
    potential = serializers.CharField()
    subject = serializers.CharField()
    headline = serializers.CharField()
    description = serializers.CharField()
    instruction = serializers.CharField()
    shakemap = serializers.CharField(allow_blank=True, required=False)
    timesent = serializers.CharField()


# ── GeoJSON event helpers (Mon3 / Yr5) ───────────────────────


class GeoEventPropertiesSerializer(serializers.Serializer):
    """Properties for Mon3 / Yr5 GeoJSON features (identical schema)."""

    status = serializers.CharField()
    depth = serializers.FloatField()
    place = serializers.CharField()
    mag = serializers.FloatField()
    time = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M:%S.%f"])
    id = serializers.CharField()
    fase = serializers.IntegerField()


class GeoEventFeatureSerializer(serializers.Serializer):
    """GeoJSON ``Feature`` for Mon3 / Yr5."""

    geometry = GeoPointSerializer()
    type = serializers.CharField()
    properties = GeoEventPropertiesSerializer()


# ── Fault serializers ────────────────────────────────────────


class FaultGeometrySerializer(serializers.Serializer):
    type = serializers.CharField()
    coordinates = serializers.JSONField()


class FaultFeatureSerializer(serializers.Serializer):
    type = serializers.CharField()
    properties = serializers.DictField()
    geometry = FaultGeometrySerializer()


class FaultCatalogSerializer(serializers.Serializer):
    type = serializers.CharField()
    name = serializers.CharField(required=False, allow_blank=True)
    crs = serializers.DictField(required=False)
    features = FaultFeatureSerializer(many=True)


# ── History serializers ──────────────────────────────────────


class HistoryRecordSerializer(serializers.Serializer):
    timestamp = serializers.DateTimeField(input_formats=["%Y-%m-%d %H:%M:%S"])
    ot_minutes = serializers.FloatField(allow_null=True, required=False)
    latitude = serializers.FloatField(allow_null=True, required=False)
    longitude = serializers.FloatField(allow_null=True, required=False)
    depth = serializers.FloatField(allow_null=True, required=False)
    phase_count = serializers.IntegerField(allow_null=True, required=False)
    mag_type = serializers.CharField(allow_blank=True, required=False)
    magnitude = serializers.FloatField(allow_null=True, required=False)
    mag_count = serializers.IntegerField(allow_null=True, required=False)
    status = serializers.CharField(allow_blank=True, required=False)


class HistoryResponseSerializer(serializers.Serializer):
    eventid = serializers.CharField()
    records = HistoryRecordSerializer(many=True)


# ── Global sensor serializers ────────────────────────────────


class GlobalPropertiesSerializer(serializers.Serializer):
    description = serializers.CharField()
    net = serializers.CharField()
    sta = serializers.CharField()


class GlobalFeatureSerializer(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField()
    geometry = GeoPointSerializer()
    properties = GlobalPropertiesSerializer()


class GlobalCatalogSerializer(serializers.Serializer):
    features = GlobalFeatureSerializer(many=True)


# ── Seismic sensor serializers ───────────────────────────────


class SeismicPropertiesSerializer(serializers.Serializer):
    id = serializers.CharField()
    stakeholder = serializers.CharField()
    uptbmkg = serializers.CharField()


class SeismicFeatureSerializer(serializers.Serializer):
    type = serializers.CharField()
    properties = SeismicPropertiesSerializer()
    geometry = GeoPointSerializer()


class SeismicCatalogSerializer(serializers.Serializer):
    type = serializers.CharField()
    features = SeismicFeatureSerializer(many=True)


# ── Mon3 / Yr5 (identical GeoJSON catalog schema) ───────────


class Mon3CatalogSerializer(serializers.Serializer):
    type = serializers.CharField()
    features = GeoEventFeatureSerializer(many=True)


class Yr5CatalogSerializer(Mon3CatalogSerializer):
    """Yr5 shares its schema with Mon3."""


# ── M5 alert ─────────────────────────────────────────────────


class M5AlertSerializer(BaseAlertEnvelopeSerializer):
    info = BaseAlertInfoSerializer(many=True)


# ── Felt alert ───────────────────────────────────────────────


class FeltInfoSerializer(BaseAlertInfoSerializer):
    felt = serializers.CharField()


class FeltAlertSerializer(BaseAlertEnvelopeSerializer):
    info = FeltInfoSerializer(many=True)


# ── Tsunami alert ────────────────────────────────────────────


class TsunamiWzAreaSerializer(serializers.Serializer):
    province = serializers.CharField(allow_blank=True, required=False)
    district = serializers.CharField(allow_blank=True, required=False)
    level = serializers.CharField(allow_blank=True, required=False)
    date = serializers.DateField(input_formats=["%d-%m-%Y", "%d-%m-%y"], required=False)
    time = serializers.CharField(allow_blank=True, required=False)


class TsunamiObsAreaSerializer(serializers.Serializer):
    location = serializers.CharField(allow_blank=True, required=False)
    loclatitude = serializers.CharField(allow_blank=True, required=False)
    loclongitude = serializers.CharField(allow_blank=True, required=False)
    height = serializers.FloatField(allow_null=True, required=False)
    date = serializers.DateField(input_formats=["%d-%m-%Y", "%d-%m-%y"], required=False)
    time = serializers.CharField(allow_blank=True, required=False)


class TsunamiInfoSerializer(BaseAlertInfoSerializer):
    point = AlertPointSerializer(required=False)
    wzmap = serializers.CharField(allow_blank=True, required=False)
    ttmap = serializers.CharField(allow_blank=True, required=False)
    sshmap = serializers.CharField(allow_blank=True, required=False)
    instruction1 = serializers.CharField(allow_blank=True, required=False)
    instruction2 = serializers.CharField(allow_blank=True, required=False)
    instruction3 = serializers.CharField(allow_blank=True, required=False)
    wzarea = TsunamiWzAreaSerializer(many=True, required=False)
    obsarea = TsunamiObsAreaSerializer(many=True, required=False)


class TsunamiAlertSerializer(BaseAlertEnvelopeSerializer):
    info = TsunamiInfoSerializer(many=True)


# ── Latest earthquake alert ──────────────────────────────────


class InfoSerializer(BaseAlertInfoSerializer):
    """Latest alert info — adds ``felt`` and tightens ``date`` format."""

    date = serializers.DateField(input_formats=["%d-%m-%y"])
    magnitude = serializers.FloatField()
    shakemap = serializers.CharField()
    felt = serializers.CharField(required=False, allow_blank=True)


class EarthquakeAlertSerializer(BaseAlertEnvelopeSerializer):
    info = InfoSerializer()


# ── Damage / catalog ─────────────────────────────────────────


class PropertiesSerializer(serializers.Serializer):
    lokasi = serializers.CharField()
    ot_utc = serializers.TimeField()
    pusat_gempa = serializers.CharField()
    tsunami = IndonesianBooleanField()
    id_event = serializers.CharField()
    korban_kerusakan = serializers.CharField()
    depth = serializers.IntegerField()
    mag = serializers.FloatField()
    date = serializers.DateField(input_formats=["%d-%m-%Y", "%Y/%m/%d"])
    sumber = serializers.CharField()
    dirasakan = serializers.CharField()


class FeatureSerializer(serializers.Serializer):
    geometry = GeoPointSerializer()
    type = serializers.CharField()
    properties = PropertiesSerializer()


class DamageSerializer(serializers.Serializer):
    type = serializers.CharField()
    features = FeatureSerializer(many=True)


# ── Realtime ─────────────────────────────────────────────────


class RealtimeEventSerializer(serializers.Serializer):
    eventid = serializers.CharField()
    status = serializers.CharField()
    datetime = serializers.DateTimeField(
        source="waktu",
        input_formats=["%Y/%m/%d %H:%M:%S.%f"],
    )
    latitude = serializers.FloatField(source="lintang")
    longitude = serializers.FloatField(source="bujur")
    depth = serializers.IntegerField(source="dalam")
    mag = serializers.FloatField()
    fokal = serializers.CharField()
    area = serializers.CharField()


class RealtimeCatalogSerializer(serializers.Serializer):
    events = RealtimeEventSerializer(many=True)
