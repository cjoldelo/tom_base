from django.db import models
from django import forms
from django.urls import reverse
from django.conf import settings
from django.forms.models import model_to_dict

from skyfield.api import Topos, load, Star, utc
from skyfield.elementslib import OsculatingElements
from datetime import datetime, timezone, timedelta

from tom_observations import facility


GLOBAL_TARGET_FIELDS = ['identifier', 'name', 'designation', 'type']

SIDEREAL_FIELDS = GLOBAL_TARGET_FIELDS + [
    'ra', 'dec', 'epoch', 'pm_ra', 'pm_dec',
    'galactic_lng', 'galactic_lat', 'distance', 'distance_err'
]

NON_SIDEREAL_FIELDS = GLOBAL_TARGET_FIELDS + [
    'mean_anomaly', 'arg_of_perihelion',
    'lng_asc_node', 'inclination', 'mean_daily_motion', 'semimajor_axis',
    'ephemeris_period', 'ephemeris_period_err', 'ephemeris_epoch',
    'ephemeris_epoch_err'
]


class Target(models.Model):
    SIDEREAL = 'SIDEREAL'
    NON_SIDEREAL = 'NON_SIDEREAL'
    TARGET_TYPES = ((SIDEREAL, 'Sidereal'), (NON_SIDEREAL, 'Non-sidereal'))

    identifier = models.CharField(max_length=100, verbose_name='Identifier', help_text='The identifier for this object, e.g. Kelt-16b.')
    name = models.CharField(max_length=100, default='', verbose_name='Name', help_text='The name of this target e.g. Barnard\'s star.')
    type = models.CharField(max_length=100, choices=TARGET_TYPES, verbose_name='Target Type', help_text='The type of this target.')
    designation = models.CharField(max_length=100, default='', verbose_name='Designation', help_text='Designation of this target.')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Time Created', help_text='The time which this target was created in the TOM database.')
    modified = models.DateTimeField(auto_now=True, verbose_name='Last Modified', help_text='The time which this target was changed in the TOM database.')
    ra = models.FloatField(null=True, blank=True, verbose_name='Right Ascension', help_text='Right Ascension, in degrees.')
    dec = models.FloatField(null=True, blank=True, verbose_name='Declination', help_text='Declination, in degrees.')
    epoch = models.FloatField(null=True, blank=True, verbose_name='Epoch of Elements', help_text='Julian Years. Max 2100.')
    parallax = models.FloatField(null=True, blank=True, verbose_name='Parallax', help_text='Parallax, in milliarcseconds.')
    pm_ra = models.FloatField(null=True, blank=True, verbose_name='Proper Motion (RA)', help_text='Proper Motion: RA. Milliarsec/year.')
    pm_dec = models.FloatField(null=True, blank=True, verbose_name='Proper Motion (Declination)', help_text='Proper Motion: Dec. Milliarsec/year.')
    galactic_lng = models.FloatField(null=True, blank=True, verbose_name='Galactic Longitude', help_text='Galactic Longitude in degrees.')
    galactic_lat = models.FloatField(null=True, blank=True, verbose_name='Galactic Latitude', help_text='Galactic Latitude in degrees.')
    distance = models.FloatField(null=True, blank=True, verbose_name='Distance', help_text='Parsecs.')
    distance_err = models.FloatField(null=True, blank=True, verbose_name='Distance Error', help_text='Parsecs.')
    mean_anomaly = models.FloatField(null=True, blank=True, verbose_name='Mean Anomaly', help_text='Angle in degrees.')
    arg_of_perihelion = models.FloatField(null=True, blank=True, verbose_name='Argument of Perihelion', help_text='Argument of Perhihelion. J2000. Degrees.')
    eccentricity = models.FloatField(null=True, blank=True, verbose_name='Eccentricity', help_text='Eccentricity')
    lng_asc_node = models.FloatField(null=True, blank=True, verbose_name='Longitude of Ascending Node', help_text='Longitude of Ascending Node. J2000. Degrees.')
    inclination = models.FloatField(null=True, blank=True, verbose_name='Inclination to the ecliptic', help_text='Inclination to the ecliptic. J2000. Degrees.')
    mean_daily_motion = models.FloatField(null=True, blank=True, verbose_name='Mean Daily Motion', help_text='Degrees per day.')
    semimajor_axis = models.FloatField(null=True, blank=True, verbose_name='Semimajor Axis', help_text='In AU')
    ephemeris_period = models.FloatField(null=True, blank=True, verbose_name='Ephemeris Period', help_text='Days')
    ephemeris_period_err = models.FloatField(null=True, blank=True, verbose_name='Ephemeris Period Error', help_text='Days')
    ephemeris_epoch = models.FloatField(null=True, blank=True, verbose_name='Ephemeris Epoch', help_text='Days')
    ephemeris_epoch_err = models.FloatField(null=True, blank=True, verbose_name='Ephemeris Epoch Error', help_text='Days')

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.identifier

    def get_absolute_url(self):
        return reverse('targets:detail', kwargs={'pk': self.id})

    def as_dict(self):
        if self.type == self.SIDEREAL:
            fields_for_type = SIDEREAL_FIELDS
        elif self.type == self.NON_SIDEREAL:
            fields_for_type = NON_SIDEREAL_FIELDS
        else:
            fields_for_type = GLOBAL_TARGET_FIELDS

        return model_to_dict(self, fields=fields_for_type)

    def get_object_instance_for_type(self):
        if type == self.SIDEREAL:
            return Star(ra_hours=self.ra,
                        dec_degrees=self.dec,
                        ra_mas_per_year=self.pm_ra,
                        dec_mas_per_year=self.pm_dec,
                        epoch=self.epoch,
                        parallax_mas=self.parallax)
        elif type == self.NON_SIDEREAL:
            return OsculatingElements(eccentricity=self.eccentricity,
                                    inclination=self.inclination,
                                    longitude_of_ascending_node=self.lng_asc_node
            )

    def get_visibility(self, start_time, end_time, interval):
        planets = load('de421.bsp')
        ts = load.timescale()
        for observing_facility in facility.get_service_classes():
            sites = facility.get_service_class(observing_facility).get_observing_sites()
            for site, site_details in sites.items():
                observing_site = planets['earth'] + Topos(site_details.get('latitude'), site_details.get('longitude'))
                #TODO: allow for other object types
                #TODO: add weather support
                #TODO: add parallax support
                #TODO: ensure all fields have defaults to avoid exceptions--parallax may not be necessary
                target_object = self.get_object_instance_for_type()
                time_range = ts.utc([start_time + timedelta(minutes=i) for i in range(0, 60, interval)])
                astrometric_position = observing_site.at(time_range).observe(target_object)
                apparent_position = astrometric_position.apparent()
                alt, az, distance = apparent_position.altaz()
                print(alt)
                print(az)
                print(distance)
                print()
        pass


class TargetExtra(models.Model):
    target = models.ForeignKey(Target, on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.TextField()


class TargetList(models.Model):
    name = models.CharField(max_length=200, help_text='The name of the target list.')
    targets = models.ManyToManyField(Target)
    created = models.DateTimeField(auto_now_add=True, help_text='The time which this target list was created in the TOM database.')

    def __str__(self):
        return self.name
