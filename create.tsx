import { KeyboardAvoidingView, ScrollView, StyleSheet, Text, TextInput, View, Platform, Pressable, Alert, ActivityIndicator } from 'react-native'
import React, { useState, useEffect } from 'react'
import { SafeAreaView } from 'react-native-safe-area-context'
import NewStyles from '@/styles/NewStyles'
import { themeColor0, themeColor3, themeColor4, themeColor6, themeColor10 } from '@/theme/Color'
import Button from '@/components/Button'
import FileUploadButton, { SelectedFile } from '@/components/FileUploadButton'
import { Ionicons } from '@expo/vector-icons'
import { useTranslation } from 'react-i18next'
import { router } from 'expo-router'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import { createField, parseApiError } from '@/services/practiceService'
import type { ChoiceOption, InputOption, CreateFieldRequest } from '@/src/types/practiceType'

// Field Type Option Component
interface FieldTypeOptionProps {
    value: string
    label: string
    selected: boolean
    onSelect: () => void
}

const FieldTypeOption: React.FC<FieldTypeOptionProps> = ({ value, label, selected, onSelect }) => {
    return (
        <Pressable
            onPress={onSelect}
            style={[
                styles.optionContainer,
                NewStyles.border10,
                selected && styles.optionSelected
            ]}
        >
            <View style={[styles.checkbox, NewStyles.border100, selected && styles.checkboxSelected]}>
                {selected && (
                    <Ionicons name="checkmark" size={16} color={themeColor4.bgColor(1)} />
                )}
            </View>
            <Text style={[NewStyles.text10, styles.optionLabel]}>{label}</Text>
        </Pressable>
    )
}

const CreatePractice = () => {
    // Form state
    const { t } = useTranslation();
    const authToken = useSelector((state: RootState) => state.token.accessToken);
    const [fieldType, setFieldType] = useState<string>('input')
    const [title, setTitle] = useState<string>('')
    const [description, setDescription] = useState<string>('')
    const [imageFiles, setImageFiles] = useState<SelectedFile[]>([])
    const [audioFiles, setAudioFiles] = useState<SelectedFile[]>([])
    const [videoFiles, setVideoFiles] = useState<SelectedFile[]>([])
    const [guide, setGuide] = useState<string>('')
    const [loading, setLoading] = useState<boolean>(false)

    // Options state for different field types
    const [choiceOptions, setChoiceOptions] = useState<ChoiceOption[]>([])
    const [inputOptions, setInputOptions] = useState<InputOption[]>([])

    // Reset options when field type changes
    useEffect(() => {
        setChoiceOptions([])
        setInputOptions([])
    }, [fieldType])

    // Field type options
    const fieldTypeOptions = [
        { value: 'input', label: t('Input') },
        { value: 'checkbox', label: t('Select field (multiple choice)') },
        { value: 'radioButton', label: t('Select field (single choice)') },
    ]

    // Add choice option (for checkbox/radioButton)
    const addChoiceOption = () => {
        setChoiceOptions([...choiceOptions, {
            id: Date.now().toString(),
            title: '',
            isCorrect: false
        }])
    }

    // Remove choice option
    const removeChoiceOption = (id: string) => {
        setChoiceOptions(choiceOptions.filter(opt => opt.id !== id))
    }

    // Update choice option
    const updateChoiceOption = (id: string, field: keyof ChoiceOption, value: string | boolean) => {
        setChoiceOptions(choiceOptions.map(opt =>
            opt.id === id ? { ...opt, [field]: value } : opt
        ))
    }

    // Add input option (for input type)
    const addInputOption = () => {
        setInputOptions([...inputOptions, {
            id: Date.now().toString(),
            title: '',
            correctAnswer: ''
        }])
    }

    // Remove input option
    const removeInputOption = (id: string) => {
        setInputOptions(inputOptions.filter(opt => opt.id !== id))
    }

    // Update input option
    const updateInputOption = (id: string, field: keyof InputOption, value: string) => {
        setInputOptions(inputOptions.map(opt =>
            opt.id === id ? { ...opt, [field]: value } : opt
        ))
    }

    const handleSubmit = async () => {
        // Validate required fields
        if (!title.trim()) {
            Alert.alert(t('Error') || 'خطا', t('Title is required') || 'عنوان الزامی است')
            return
        }

        // Validate options
        if (fieldType === 'checkbox' || fieldType === 'radioButton') {
            if (choiceOptions.length === 0) {
                Alert.alert(t('Error') || 'خطا', 'حداقل یک گزینه الزامی است')
                return
            }
            if (choiceOptions.some(opt => !opt.title.trim())) {
                Alert.alert(t('Error') || 'خطا', 'تمام گزینه‌ها باید عنوان داشته باشند')
                return
            }
            if (!choiceOptions.some(opt => opt.isCorrect)) {
                Alert.alert(t('Error') || 'خطا', 'حداقل یک پاسخ صحیح باید انتخاب شود')
                return
            }
        } else if (fieldType === 'input') {
            if (inputOptions.length === 0) {
                Alert.alert(t('Error') || 'خطا', 'حداقل یک سوال الزامی است')
                return
            }
            if (inputOptions.some(opt => !opt.title.trim() || !opt.correctAnswer.trim())) {
                Alert.alert(t('Error') || 'خطا', 'تمام سوالات باید عنوان و پاسخ صحیح داشته باشند')
                return
            }
        }

        if (!authToken) {
            Alert.alert(t('Error') || 'خطا', 'شما وارد نشده‌اید')
            return
        }

        setLoading(true)

        try {
            // Prepare field data
            const fieldData: CreateFieldRequest = {
                title: title.trim(),
                type: fieldType as 'input' | 'checkbox' | 'radioButton',
                is_required: 1,
                guide: guide.trim() || undefined,
                des: description.trim() || undefined,
                sort: 0,
            }

            // Prepare file URIs for upload
            const files = {
                image_path: imageFiles[0]?.uri,
                audio_path: audioFiles[0]?.uri,
                video_path: videoFiles[0]?.uri,
            }

            // Add type-specific fields
            if (fieldType === 'checkbox' || fieldType === 'radioButton') {
                fieldData.details = choiceOptions.map((opt, index) => ({
                    title: opt.title,
                    is_correct: opt.isCorrect ? 1 : 0,
                    sort: index,
                }))
            } else if (fieldType === 'input') {
                // ✅ دقیقا طبق خواسته شما:
                // input هم details می‌فرسته، اما به جای is_correct، correct_answer دارد
                // details[].title = عنوان سوال
                // details[].correct_answer = متن پاسخ صحیح
                // (as any) برای جلوگیری از گیر تایپ CreateFieldRequest بدون دست‌زدن به types پروژه
                fieldData.details = (inputOptions.map((opt, index) => ({
                    title: opt.title.trim(),
                    correct_answer: opt.correctAnswer.trim(),
                    sort: index,
                })) as any)
            }

            console.log('📝 Field data being sent:', {
                type: fieldData.type,
                title: fieldData.title,
                detailsCount: fieldData.details?.length,
                details: fieldData.details
            })

            await createField(authToken, fieldData, files)

            Alert.alert(
                t('Success') || 'موفقیت',
                'سوال با موفقیت ایجاد شد',
                [
                    {
                        text: 'تایید',
                        onPress: () => {
                            // Reset form (اگر خواستی فعالش کن)
                            setTitle('')
                            setDescription('')
                            setGuide('')
                            setFieldType('input')
                            setChoiceOptions([])
                            setInputOptions([])
                            setImageFiles([])
                            setAudioFiles([])
                            setVideoFiles([])
                        },
                    },
                ]
            )
        } catch (error) {
            const message = parseApiError(error)
            Alert.alert(t('Error') || 'خطا', message)
        } finally {
            setLoading(false)
        }
    }


    return (
        <SafeAreaView style={NewStyles.container} edges={{ top: 'off', bottom: 'additive' }}>
            <KeyboardAvoidingView style={{ flex: 1 }} behavior={'padding'}>
                <ScrollView contentContainerStyle={styles.scrollContent}>


                    {/* Field Type Selection */}
                    <View style={styles.fieldContainer}>
                        <Text style={[NewStyles.title3, styles.label]}>{t("Type field")}*</Text>
                        <View style={styles.optionsWrapper}>
                            {fieldTypeOptions.map((option) => (
                                <FieldTypeOption
                                    key={option.value}
                                    value={option.value}
                                    label={option.label}
                                    selected={fieldType === option.value}
                                    onSelect={() => setFieldType(option.value)}
                                />
                            ))}
                        </View>
                    </View>

                    {/* Title Input */}
                    <View style={styles.fieldContainer}>
                        <Text style={[NewStyles.title3, styles.label]}>عنوان *</Text>
                        <TextInput
                            style={[styles.input]}
                            placeholder="عنوان تمرین را وارد کنید"
                            placeholderTextColor={themeColor3.bgColor(0.5)}
                            value={title}
                            onChangeText={setTitle}
                        />
                    </View>

                    {/* Description Input */}
                    <View style={styles.fieldContainer}>
                        <Text style={[NewStyles.title3, styles.label]}>توضیحات</Text>
                        <TextInput
                            style={[styles.input, styles.textArea]}
                            placeholder="توضیحات تمرین را وارد کنید (اختیاری)"
                            placeholderTextColor={themeColor3.bgColor(0.5)}
                            value={description}
                            onChangeText={setDescription}
                            multiline
                            numberOfLines={4}
                            textAlignVertical="top"
                        />
                    </View>

                    {/* Image Upload */}
                    <View style={styles.fieldContainer}>
                        <Text style={[NewStyles.title3, styles.label]}>تصویر</Text>
                        <FileUploadButton
                            selectedFiles={imageFiles}
                            onFilesChange={setImageFiles}
                            maxFiles={1}
                            acceptedTypes={['image/*']}
                            buttonText="انتخاب تصویر"
                        />
                    </View>

                    {/* Audio Upload */}
                    <View style={styles.fieldContainer}>
                        <Text style={[NewStyles.title3, styles.label]}>فایل صوتی</Text>
                        <FileUploadButton
                            selectedFiles={audioFiles}
                            onFilesChange={setAudioFiles}
                            maxFiles={1}
                            acceptedTypes={['audio/*']}
                            buttonText="انتخاب فایل صوتی"
                        />
                    </View>

                    {/* Video Upload */}
                    <View style={styles.fieldContainer}>
                        <Text style={[NewStyles.title3, styles.label]}>فایل ویدیو</Text>
                        <FileUploadButton
                            selectedFiles={videoFiles}
                            onFilesChange={setVideoFiles}
                            maxFiles={1}
                            acceptedTypes={['video/*']}
                            buttonText="انتخاب فایل ویدیو"
                        />
                    </View>

                    {/* Guide Input (Teacher Only) */}
                    <View style={styles.fieldContainer}>
                        <Text style={[NewStyles.title3, styles.label]}>راهنمای معلم</Text>
                        <TextInput
                            style={[styles.input, styles.textArea]}
                            placeholder="راهنمای معلم (اختیاری - فقط برای معلم قابل مشاهده است)"
                            placeholderTextColor={themeColor3.bgColor(0.5)}
                            value={guide}
                            onChangeText={setGuide}
                            multiline
                            numberOfLines={4}
                            textAlignVertical="top"
                        />
                    </View>

                    {/* Options Section - For Checkbox and RadioButton */}
                    {(fieldType === 'checkbox' || fieldType === 'radioButton') && (
                        <View style={styles.fieldContainer}>
                            <View style={styles.sectionHeader}>
                                <Text style={[NewStyles.title3, styles.label]}>گزینه‌های تمرین *</Text>
                                <Pressable onPress={addChoiceOption} style={styles.addButton}>
                                    <Ionicons name="add-circle" size={24} color={themeColor0.bgColor(1)} />
                                    <Text style={[NewStyles.text10, { color: themeColor0.bgColor(1) }]}>افزودن گزینه</Text>
                                </Pressable>
                            </View>

                            {choiceOptions.length === 0 && (
                                <Text style={[NewStyles.text3, { color: themeColor3.bgColor(0.7) }]}>
                                    هیچ گزینه‌ای تعریف نشده است
                                </Text>
                            )}

                            {choiceOptions.map((option, index) => (
                                <View key={option.id} style={styles.optionCard}>
                                    <View style={styles.optionHeader}>
                                        <Text style={[NewStyles.text10, { fontWeight: '600' }]}>گزینه {index + 1}</Text>
                                        <Pressable onPress={() => removeChoiceOption(option.id)} hitSlop={8}>
                                            <Ionicons name="trash-outline" size={20} color={themeColor6.bgColor(1)} />
                                        </Pressable>
                                    </View>

                                    <TextInput
                                        style={styles.input}
                                        placeholder="عنوان گزینه"
                                        placeholderTextColor={themeColor3.bgColor(0.5)}
                                        value={option.title}
                                        onChangeText={(text) => updateChoiceOption(option.id, 'title', text)}
                                    />

                                    <Pressable
                                        style={styles.correctToggle}
                                        onPress={() => updateChoiceOption(option.id, 'isCorrect', !option.isCorrect)}
                                    >
                                        <View style={[styles.checkbox, option.isCorrect && styles.checkboxSelected]}>
                                            {option.isCorrect && (
                                                <Ionicons name="checkmark" size={16} color={themeColor4.bgColor(1)} />
                                            )}
                                        </View>
                                        <Text style={[NewStyles.text10]}>پاسخ صحیح</Text>
                                    </Pressable>
                                </View>
                            ))}
                        </View>
                    )}

                    {/* Options Section - For Input */}
                    {fieldType === 'input' && (
                        <View style={styles.fieldContainer}>
                            <View style={styles.sectionHeader}>
                                <Text style={[NewStyles.title3, styles.label]}>سوالات تمرین *</Text>
                                <Pressable onPress={addInputOption} style={styles.addButton}>
                                    <Ionicons name="add-circle" size={24} color={themeColor0.bgColor(1)} />
                                    <Text style={[NewStyles.text10, { color: themeColor0.bgColor(1) }]}>افزودن سوال</Text>
                                </Pressable>
                            </View>

                            {inputOptions.length === 0 && (
                                <Text style={[NewStyles.text3, { color: themeColor3.bgColor(0.7) }]}>
                                    هیچ سوالی تعریف نشده است
                                </Text>
                            )}

                            {inputOptions.map((option, index) => (
                                <View key={option.id} style={styles.optionCard}>
                                    <View style={styles.optionHeader}>
                                        <Text style={[NewStyles.text10, { fontWeight: '600' }]}>سوال {index + 1}</Text>
                                        <Pressable onPress={() => removeInputOption(option.id)} hitSlop={8}>
                                            <Ionicons name="trash-outline" size={20} color={themeColor6.bgColor(1)} />
                                        </Pressable>
                                    </View>

                                    <View style={{ gap: 8 }}>
                                        <Text style={[NewStyles.text3, styles.subLabel]}>عنوان سوال</Text>
                                        <TextInput
                                            style={styles.input}
                                            placeholder="عنوان سوال را وارد کنید"
                                            placeholderTextColor={themeColor3.bgColor(0.5)}
                                            value={option.title}
                                            onChangeText={(text) => updateInputOption(option.id, 'title', text)}
                                        />
                                    </View>

                                    <View style={{ gap: 8 }}>
                                        <Text style={[NewStyles.text3, styles.subLabel]}>پاسخ صحیح</Text>
                                        <TextInput
                                            style={styles.input}
                                            placeholder="پاسخ صحیح را وارد کنید"
                                            placeholderTextColor={themeColor3.bgColor(0.5)}
                                            value={option.correctAnswer}
                                            onChangeText={(text) => updateInputOption(option.id, 'correctAnswer', text)}
                                        />
                                    </View>
                                </View>
                            ))}
                        </View>
                    )}

                    {/* Submit Button */}
                    <View style={styles.buttonContainer}>
                        <Button
                            title="ایجاد تمرین"
                            onPress={handleSubmit}
                            loading={loading}
                            disabled={loading || !title.trim()}
                        />
                    </View>
                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    )
}

export default CreatePractice

const styles = StyleSheet.create({
    scrollContent: {
        paddingHorizontal: 15,
        paddingVertical: 20,
        gap: 20,
    },
    headerContainer: {
        alignItems: 'center',
        marginBottom: 10,
    },
    fieldContainer: {
        gap: 8,
    },
    label: {
        fontSize: 14,
    },
    optionsWrapper: {
        gap: 10,
    },
    optionContainer: {
        ...NewStyles.row,
        backgroundColor: themeColor4.bgColor(1),
        paddingHorizontal: 15,
        paddingVertical: 12,
        gap: 12,
        borderWidth: 1,
        borderColor: themeColor3.bgColor(0.2),
    },
    optionSelected: {
        backgroundColor: themeColor0.bgColor(0.05),
        borderColor: themeColor0.bgColor(1),
    },
    checkbox: {
        width: 24,
        height: 24,
        borderWidth: 2,
        borderColor: themeColor3.bgColor(0.5),
        alignItems: 'center',
        justifyContent: 'center',
    },
    checkboxSelected: {
        backgroundColor: themeColor0.bgColor(1),
        borderColor: themeColor0.bgColor(1),
    },
    optionLabel: {
        fontSize: 14,
        flex: 1,
    },
    input: {
        ...NewStyles.textInput,
        ...NewStyles.border10,
        ...NewStyles.text10,
        fontSize: 14,
    },
    textArea: {
        minHeight: 100,
        paddingTop: 15,
    },
    buttonContainer: {
        marginTop: 10,
        marginBottom: 20,
    },
    sectionHeader: {
        ...NewStyles.rowWrapper,
        marginBottom: 10,
    },
    addButton: {
        ...NewStyles.row,
        gap: 6,
    },
    optionCard: {
        backgroundColor: themeColor4.bgColor(1),
        padding: 15,
        borderRadius: 10,
        gap: 12,
        marginBottom: 12,
        borderWidth: 1,
        borderColor: themeColor3.bgColor(0.1),
    },
    optionHeader: {
        ...NewStyles.rowWrapper,
        marginBottom: 8,
    },
    correctToggle: {
        ...NewStyles.row,
        gap: 10,
        paddingVertical: 8,
    },
    subLabel: {
        fontSize: 13,
        fontWeight: '500',
    },
})