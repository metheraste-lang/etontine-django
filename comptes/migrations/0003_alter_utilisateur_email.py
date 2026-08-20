from django.db import migrations, models


def corriger_emails_vides(apps, schema_editor):
    Utilisateur = apps.get_model('comptes', 'Utilisateur')
    for utilisateur in Utilisateur.objects.filter(email=''):
        utilisateur.email = f"utilisateur{utilisateur.id}@etontinetchad.local"
        utilisateur.save(update_fields=['email'])


def ne_rien_faire(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0002_utilisateur_solde'),
    ]

    operations = [
        migrations.RunPython(corriger_emails_vides, ne_rien_faire),
        migrations.AlterField(
            model_name='utilisateur',
            name='email',
            field=models.EmailField(help_text="Adresse e-mail, utilisée pour la réinitialisation du mot de passe.", max_length=254, unique=True),
        ),
    ]
