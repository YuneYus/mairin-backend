from django.db import migrations


class Migration(migrations.Migration):
    """Renombres explícitos para no perder datos (makemigrations los trataría como borrar y crear)."""

    dependencies = [("api", "0006_copy_legacy_data")]

    operations = [
        migrations.RenameModel("Cirugia", "Surgery"),
        migrations.RenameField("profile", "cycle_reset_date", "cycle_tracking_start"),
    ]
