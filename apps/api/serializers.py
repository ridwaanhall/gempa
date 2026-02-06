from rest_framework import serializers

# custom fields
class IndonesianBooleanField(serializers.BooleanField):
    """Boolean field that treats 'Ya'/'Tidak' (case-insensitive) as True/False."""
    TRUE_VALUES = serializers.BooleanField.TRUE_VALUES | {"ya"}
    FALSE_VALUES = serializers.BooleanField.FALSE_VALUES | {"tidak"}


# latest
class PointSerializer(serializers.Serializer):
    coordinates = serializers.CharField()

class InfoSerializer(serializers.Serializer):
    event = serializers.CharField()
    date = serializers.DateField(
        input_formats=["%d-%m-%y"]
    )
    time = serializers.CharField()
    point = PointSerializer()
    latitude = serializers.CharField()
    longitude = serializers.CharField()
    magnitude = serializers.FloatField()
    depth = serializers.CharField()
    area = serializers.CharField()
    eventid = serializers.IntegerField()
    potential = serializers.CharField()
    subject = serializers.CharField()
    headline = serializers.CharField()
    description = serializers.CharField()
    instruction = serializers.CharField()
    shakemap = serializers.CharField()
    felt = serializers.CharField()
    timesent = serializers.CharField()

class EarthquakeAlertSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    sender = serializers.CharField()
    sent = serializers.CharField()
    status = serializers.CharField()
    msgType = serializers.CharField()
    scope = serializers.CharField()
    code = serializers.CharField()
    info = InfoSerializer()


# catalog
class GeometrySerializer(serializers.Serializer):
    type = serializers.CharField()
    coordinates = serializers.ListField(child=serializers.FloatField())

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
    geometry = GeometrySerializer()
    type = serializers.CharField()
    properties = PropertiesSerializer()

class CatalogSerializer(serializers.Serializer):
    type = serializers.CharField()
    features = FeatureSerializer(many=True)


# realtime
class RealtimeEventSerializer(serializers.Serializer):
    eventid = serializers.CharField()
    status = serializers.CharField()
    datetime = serializers.DateTimeField(
        source="waktu",
        input_formats=["%Y/%m/%d %H:%M:%S.%f"]
    )
    latitude = serializers.FloatField(source="lintang")
    longitude = serializers.FloatField(source="bujur")
    depth = serializers.IntegerField(source="dalam")
    mag = serializers.FloatField()
    fokal = serializers.CharField()
    area = serializers.CharField()

class RealtimeCatalogSerializer(serializers.Serializer):
    events = RealtimeEventSerializer(many=True)
