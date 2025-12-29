from modeltranslation.translator import translator, TranslationOptions
from .models import TeacherAvailability, TeachingSubject, ClassBooking, TeacherWallet, ClassRevenue, WithdrawalRequest, WalletTransaction, StudentTransaction


class TeacherAvailabilityTranslationOptions(TranslationOptions):
    fields = ('notes',)

translator.register(TeacherAvailability, TeacherAvailabilityTranslationOptions)


class TeachingSubjectTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

translator.register(TeachingSubject, TeachingSubjectTranslationOptions)


class ClassRevenue_TranslationOptions(TranslationOptions):
    fields = ('notes',)

translator.register(ClassRevenue, ClassRevenue_TranslationOptions)


class WithdrawalRequestTranslationOptions(TranslationOptions):
    fields = ('notes', 'admin_notes')

translator.register(WithdrawalRequest, WithdrawalRequestTranslationOptions)


class WalletTransactionTranslationOptions(TranslationOptions):
    fields = ('description', 'admin_note')

translator.register(WalletTransaction, WalletTransactionTranslationOptions)


class StudentTransactionTranslationOptions(TranslationOptions):
    fields = ('description',)

translator.register(StudentTransaction, StudentTransactionTranslationOptions)
