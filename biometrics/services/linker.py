from biometrics.models import BiometricRecord

class BiometricLinker:

    @staticmethod
    def find_similar(fingerprint_hash):
        return BiometricRecord.objects.filter(
            fingerprint_hash__icontains=fingerprint_hash
        )
