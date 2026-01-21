#include <DotNet/Unity/Collections/LowLevel/Unsafe/NativeArrayUnsafeUtility.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>
#include <DotNet/Unity/Collections/NativeArray1.h>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/UnityEngine/Vector2.h>



namespace DotNet::Unity::Collections::LowLevel::Unsafe {

void* (*DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_QIjAavb5O6M1Tim2Rs2ohQ)(void* nativeArray, void** reinteropException) = nullptr;


template <> void* NativeArrayUnsafeUtility::GetUnsafeBufferPointerWithoutChecks<::std::uint8_t>(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& nativeArray) {
    void* reinteropException = nullptr;
    auto result = CallGetUnsafeBufferPointerWithoutChecks_QIjAavb5O6M1Tim2Rs2ohQ(nativeArray.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_VYRTjxyHQQFS6luUIZqMHQ)(void* nativeArray, void** reinteropException) = nullptr;


template <> void* NativeArrayUnsafeUtility::GetUnsafeBufferPointerWithoutChecks<::DotNet::UnityEngine::Vector3>(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector3>& nativeArray) {
    void* reinteropException = nullptr;
    auto result = CallGetUnsafeBufferPointerWithoutChecks_VYRTjxyHQQFS6luUIZqMHQ(nativeArray.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_iVtd6RQjrruzXGL_Bo80bw)(void* nativeArray, void** reinteropException) = nullptr;


template <> void* NativeArrayUnsafeUtility::GetUnsafeBufferPointerWithoutChecks<::DotNet::UnityEngine::Vector2>(const ::DotNet::Unity::Collections::NativeArray1<::DotNet::UnityEngine::Vector2>& nativeArray) {
    void* reinteropException = nullptr;
    auto result = CallGetUnsafeBufferPointerWithoutChecks_iVtd6RQjrruzXGL_Bo80bw(nativeArray.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_Lv3zldnuDkcZt7Gk__iYidg)(void* nativeArray, void** reinteropException) = nullptr;


template <> void* NativeArrayUnsafeUtility::GetUnsafeBufferPointerWithoutChecks<::std::int32_t>(const ::DotNet::Unity::Collections::NativeArray1<::std::int32_t>& nativeArray) {
    void* reinteropException = nullptr;
    auto result = CallGetUnsafeBufferPointerWithoutChecks_Lv3zldnuDkcZt7Gk__iYidg(nativeArray.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_dODsb2EbtCXW9Y67cYH1sg)(void* nativeArray, void** reinteropException) = nullptr;


template <> void* NativeArrayUnsafeUtility::GetUnsafeBufferPointerWithoutChecks<::std::uint16_t>(const ::DotNet::Unity::Collections::NativeArray1<::std::uint16_t>& nativeArray) {
    void* reinteropException = nullptr;
    auto result = CallGetUnsafeBufferPointerWithoutChecks_dODsb2EbtCXW9Y67cYH1sg(nativeArray.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::Unity::Collections::LowLevel::Unsafe::NativeArrayUnsafeUtility::CallGetUnsafeBufferPointerWithoutChecks_ExoUtqZSMWnuKvejW2dcYw)(void* nativeArray, void** reinteropException) = nullptr;


template <> void* NativeArrayUnsafeUtility::GetUnsafeBufferPointerWithoutChecks<::std::uint32_t>(const ::DotNet::Unity::Collections::NativeArray1<::std::uint32_t>& nativeArray) {
    void* reinteropException = nullptr;
    auto result = CallGetUnsafeBufferPointerWithoutChecks_ExoUtqZSMWnuKvejW2dcYw(nativeArray.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Collections::LowLevel::Unsafe


