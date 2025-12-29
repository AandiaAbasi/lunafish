from modeltranslation.translator import translator, TranslationOptions
from .models import (
    TeacherAvailability, 
    TeachingSubject, 
    ClassBooking,
    TeacherWallet, 
    ClassRevenue, 
    WithdrawalRequest, 
    WalletTransaction,
    StudentTransaction,
    PlatformSettings
)


class TeacherAvailabilityTranslationOptions(TranslationOptions):
    fields = ('notes',)

translator.register(TeacherAvailability, TeacherAvailabilityTranslationOptions)


class TeachingSubjectTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

translator.register(TeachingSubject, TeachingSubjectTranslationOptions)

class ClassBookingTranslationOptions(TranslationOptions):
    fields = ()

translator.register(ClassBooking, ClassBookingTranslationOptions)


class TeacherWalletTranslationOptions(TranslationOptions):
    fields = ()

translator.register(TeacherWallet, TeacherWalletTranslationOptions)


class ClassRevenueTranslationOptions(TranslationOptions):
    fields = ('notes',)

translator.register(ClassRevenue, ClassRevenueTranslationOptions)


class WithdrawalRequestTranslationOptions(TranslationOptions):
    fields = ('notes', 'admin_notes')

translator.register(WithdrawalRequest, WithdrawalRequestTranslationOptions)


class WalletTransactionTranslationOptions(TranslationOptions):
    fields = ('description', 'admin_note')

translator.register(WalletTransaction, WalletTransactionTranslationOptions)


class StudentTransactionTranslationOptions(TranslationOptions):
    fields = ('description',)

translator.register(StudentTransaction, StudentTransactionTranslationOptions)


class PlatformSettingsTranslationOptions(TranslationOptions):
    fields = ()

translator.register(PlatformSettings, PlatformSettingsTranslationOptions)
