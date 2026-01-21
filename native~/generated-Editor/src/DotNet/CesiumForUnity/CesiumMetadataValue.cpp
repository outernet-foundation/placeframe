#include <DotNet/CesiumForUnity/CesiumMetadataValue.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/System/Object.h>
#include <DotNet/CesiumForUnity/CesiumMetadataValueType.h>
#include <cstdint>
#include <DotNet/CesiumForUnity/CesiumIntVec2.h>
#include <DotNet/CesiumForUnity/CesiumIntVec3.h>
#include <DotNet/CesiumForUnity/CesiumIntVec4.h>
#include <DotNet/CesiumForUnity/CesiumUintVec2.h>
#include <DotNet/CesiumForUnity/CesiumUintVec3.h>
#include <DotNet/CesiumForUnity/CesiumUintVec4.h>
#include <DotNet/Unity/Mathematics/float2.h>
#include <DotNet/Unity/Mathematics/float3.h>
#include <DotNet/Unity/Mathematics/float4.h>
#include <DotNet/Unity/Mathematics/double2.h>
#include <DotNet/Unity/Mathematics/double3.h>
#include <DotNet/Unity/Mathematics/double4.h>
#include <DotNet/CesiumForUnity/CesiumIntMat2x2.h>
#include <DotNet/CesiumForUnity/CesiumIntMat3x3.h>
#include <DotNet/CesiumForUnity/CesiumIntMat4x4.h>
#include <DotNet/CesiumForUnity/CesiumUintMat2x2.h>
#include <DotNet/CesiumForUnity/CesiumUintMat3x3.h>
#include <DotNet/CesiumForUnity/CesiumUintMat4x4.h>
#include <DotNet/Unity/Mathematics/float2x2.h>
#include <DotNet/Unity/Mathematics/float3x3.h>
#include <DotNet/Unity/Mathematics/float4x4.h>
#include <DotNet/Unity/Mathematics/double2x2.h>
#include <DotNet/Unity/Mathematics/double3x3.h>
#include <DotNet/Unity/Mathematics/double4x4.h>
#include <DotNet/System/String.h>
#include <DotNet/CesiumForUnity/CesiumPropertyArray.h>
#include <optional>
#include "CesiumMetadataValueImpl.h"
#include <DotNet/Reinterop/ReinteropException.h>
#include <utility>
#include <DotNet/Unity/Mathematics/int2.h>
#include <DotNet/Unity/Mathematics/uint2.h>
#include <DotNet/Unity/Mathematics/int3.h>
#include <DotNet/Unity/Mathematics/uint3.h>
#include <DotNet/Unity/Mathematics/int4.h>
#include <DotNet/Unity/Mathematics/uint4.h>
#include <DotNet/Unity/Mathematics/int2x2.h>
#include <DotNet/Unity/Mathematics/uint2x2.h>
#include <DotNet/Unity/Mathematics/int3x3.h>
#include <DotNet/Unity/Mathematics/uint3x3.h>
#include <DotNet/Unity/Mathematics/int4x4.h>
#include <DotNet/Unity/Mathematics/uint4x4.h>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec2;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntVec3;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntVec4;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintVec2;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintVec3;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintVec4;
}
namespace DotNet::Unity::Mathematics {
struct float2;
}
namespace DotNet::Unity::Mathematics {
struct float3;
}
namespace DotNet::Unity::Mathematics {
struct float4;
}
namespace DotNet::Unity::Mathematics {
struct double2;
}
namespace DotNet::Unity::Mathematics {
struct double3;
}
namespace DotNet::Unity::Mathematics {
struct double4;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat2x2;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat3x3;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat4x4;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat2x2;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat3x3;
}
namespace DotNet::CesiumForUnity {
struct CesiumUintMat4x4;
}
namespace DotNet::Unity::Mathematics {
struct float2x2;
}
namespace DotNet::Unity::Mathematics {
struct float3x3;
}
namespace DotNet::Unity::Mathematics {
struct float4x4;
}
namespace DotNet::Unity::Mathematics {
struct double2x2;
}
namespace DotNet::Unity::Mathematics {
struct double3x3;
}
namespace DotNet::Unity::Mathematics {
struct double4x4;
}

namespace DotNet::CesiumForUnity {

CesiumMetadataValue::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumMetadataValue::CesiumMetadataValue(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumMetadataValue::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumMetadataValue::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumMetadataValue::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumMetadataValue::GetHandle() {
    return this->_handle;
}


void* (*CesiumMetadataValue::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


CesiumMetadataValue::CesiumMetadataValue()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


CesiumMetadataValue::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::Property_get_valueType)(void* thiz, ::DotNet::CesiumForUnity::CesiumMetadataValueType* pReturnValue, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumMetadataValueType CesiumMetadataValue::valueType() const {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumMetadataValueType result;
    Property_get_valueType((*this).GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::CesiumForUnity::CesiumMetadataValue::Property_get_objectValue)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Object CesiumMetadataValue::objectValue() const {
    void* reinteropException = nullptr;
    auto result = Property_get_objectValue((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(result));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::Property_set_objectValue)(void* thiz, void* value, void** reinteropException) = nullptr;


void CesiumMetadataValue::objectValue(const ::DotNet::System::Object& value) const {
    void* reinteropException = nullptr;
    Property_set_objectValue((*this).GetHandle().GetRaw(), value.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_K2SuSn7V3nS18YMZRRK2Lw)(void* thiz, ::std::uint8_t input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(bool input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_K2SuSn7V3nS18YMZRRK2Lw((*this).GetHandle().GetRaw(), input ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue___hk7qZfa8rr3GOj5LB___2w)(void* thiz, ::std::int8_t input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(::std::int8_t input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue___hk7qZfa8rr3GOj5LB___2w((*this).GetHandle().GetRaw(), input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_AOHrSvkQjQG6kWS8yHSsZg)(void* thiz, ::std::uint8_t input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(::std::uint8_t input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_AOHrSvkQjQG6kWS8yHSsZg((*this).GetHandle().GetRaw(), input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_GOjK0KanRT1fe9j2Ayd54A)(void* thiz, ::std::int16_t input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(::std::int16_t input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_GOjK0KanRT1fe9j2Ayd54A((*this).GetHandle().GetRaw(), input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_J5rOnxox49GXbyekWYJkRg)(void* thiz, ::std::uint16_t input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(::std::uint16_t input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_J5rOnxox49GXbyekWYJkRg((*this).GetHandle().GetRaw(), input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_hQOJfT5zVEav_dYgl__2qDA)(void* thiz, ::std::int32_t input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(::std::int32_t input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_hQOJfT5zVEav_dYgl__2qDA((*this).GetHandle().GetRaw(), input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_dwf4e0_X4__X16sg27oT_HA)(void* thiz, ::std::uint32_t input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(::std::uint32_t input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_dwf4e0_X4__X16sg27oT_HA((*this).GetHandle().GetRaw(), input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_FD9BTdwh6Rq_Uqnx3WcYzw)(void* thiz, ::std::int64_t input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(::std::int64_t input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_FD9BTdwh6Rq_Uqnx3WcYzw((*this).GetHandle().GetRaw(), input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_qWiVKY8F7ND55zOj2iwazg)(void* thiz, ::std::uint64_t input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(::std::uint64_t input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_qWiVKY8F7ND55zOj2iwazg((*this).GetHandle().GetRaw(), input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_t__W_mBs2JX7Isb90n6lv8A)(void* thiz, float input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(float input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_t__W_mBs2JX7Isb90n6lv8A((*this).GetHandle().GetRaw(), input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_2x5EigY7rzmfbErsKTGuwA)(void* thiz, double input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(double input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_2x5EigY7rzmfbErsKTGuwA((*this).GetHandle().GetRaw(), input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_1WBg__LUjCHSaTnVxWpW9hg)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntVec2* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntVec2& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_1WBg__LUjCHSaTnVxWpW9hg((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_0MPHAdrwN6Tw6ckL78VuSw)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntVec3* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntVec3& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_0MPHAdrwN6Tw6ckL78VuSw((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_SJOlUbxBoNfhxbRZHSyjCA)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntVec4* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntVec4& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_SJOlUbxBoNfhxbRZHSyjCA((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_6IVxYw6_3__T__eM__j5WVcGA)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintVec2* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintVec2& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_6IVxYw6_3__T__eM__j5WVcGA((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_AZB45d2Wd0Dhi64vRZNcpQ)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintVec3* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintVec3& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_AZB45d2Wd0Dhi64vRZNcpQ((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_CxH9s__3LeVVRneWxCIMJeQ)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintVec4* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintVec4& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_CxH9s__3LeVVRneWxCIMJeQ((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_rf6L9ndiTJQiNeSLGMcN3g)(void* thiz, const ::DotNet::Unity::Mathematics::float2* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::float2& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_rf6L9ndiTJQiNeSLGMcN3g((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_9Xqzdq684P0z1H__FquaaBA)(void* thiz, const ::DotNet::Unity::Mathematics::float3* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::float3& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_9Xqzdq684P0z1H__FquaaBA((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_VPZKsFl98vDFige9cNHc9g)(void* thiz, const ::DotNet::Unity::Mathematics::float4* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::float4& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_VPZKsFl98vDFige9cNHc9g((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue___WBWu0KVcnlBoRHTz18iQg)(void* thiz, const ::DotNet::Unity::Mathematics::double2* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::double2& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue___WBWu0KVcnlBoRHTz18iQg((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_1dZuiOwXjOp7XXu7VmYFKg)(void* thiz, const ::DotNet::Unity::Mathematics::double3* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::double3& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_1dZuiOwXjOp7XXu7VmYFKg((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_lWaGb__IpQLOSjzXG2ChwiQ)(void* thiz, const ::DotNet::Unity::Mathematics::double4* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::double4& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_lWaGb__IpQLOSjzXG2ChwiQ((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_KdIbPno6dUQIzkDlllX7cQ)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntMat2x2* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntMat2x2& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_KdIbPno6dUQIzkDlllX7cQ((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_LfJM7X33EQGf4jiLbGxqWw)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntMat3x3* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntMat3x3& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_LfJM7X33EQGf4jiLbGxqWw((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_tgJ__I0QxIjujzxx4laL3bA)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntMat4x4* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntMat4x4& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_tgJ__I0QxIjujzxx4laL3bA((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_jpn00ft20c7Tvsbl6__LFPg)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintMat2x2* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintMat2x2& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_jpn00ft20c7Tvsbl6__LFPg((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_WfkO9L_m4izzalpvtro06A)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintMat3x3* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintMat3x3& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_WfkO9L_m4izzalpvtro06A((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_OHiI21kQ_keDg54_OLHJFA)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintMat4x4* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintMat4x4& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_OHiI21kQ_keDg54_OLHJFA((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_p6Nq4_g8K2hv1dGlLZFq4A)(void* thiz, const ::DotNet::Unity::Mathematics::float2x2* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::float2x2& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_p6Nq4_g8K2hv1dGlLZFq4A((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue__dwRw4SrC5dQwg9WXOVCWA)(void* thiz, const ::DotNet::Unity::Mathematics::float3x3* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::float3x3& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue__dwRw4SrC5dQwg9WXOVCWA((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_YhLOr6l38fDvTI1UYnZdTg)(void* thiz, const ::DotNet::Unity::Mathematics::float4x4* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::float4x4& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_YhLOr6l38fDvTI1UYnZdTg((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_t4X__QJT6bJG22Rlb0EUSGg)(void* thiz, const ::DotNet::Unity::Mathematics::double2x2* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::double2x2& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_t4X__QJT6bJG22Rlb0EUSGg((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_3NklrXK7mSsrFiAUMUIpHw)(void* thiz, const ::DotNet::Unity::Mathematics::double3x3* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::double3x3& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_3NklrXK7mSsrFiAUMUIpHw((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_cbZNG6837P_AD_Fyz7orDg)(void* thiz, const ::DotNet::Unity::Mathematics::double4x4* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::Unity::Mathematics::double4x4& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_cbZNG6837P_AD_Fyz7orDg((*this).GetHandle().GetRaw(), &input, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_OekvF3gFc1nGTHuKfXsZ3g)(void* thiz, void* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::System::String& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_OekvF3gFc1nGTHuKfXsZ3g((*this).GetHandle().GetRaw(), input.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


void (*DotNet::CesiumForUnity::CesiumMetadataValue::CallSetObjectValue_wnAsp0qKwHuRGJ3ZIPvzeA)(void* thiz, void* input, void** reinteropException) = nullptr;


void CesiumMetadataValue::SetObjectValue(const ::DotNet::CesiumForUnity::CesiumPropertyArray& input) const {
    void* reinteropException = nullptr;
    CallSetObjectValue_wnAsp0qKwHuRGJ3ZIPvzeA((*this).GetHandle().GetRaw(), input.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsBoolean_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, bool* pReturnValue, void** reinteropException) = nullptr;


::std::optional<bool> CesiumMetadataValue::GetObjectAsBoolean(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    bool result;
    std::uint8_t resultIsValid = CallGetObjectAsBoolean_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsSByte_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::int8_t* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::std::int8_t> CesiumMetadataValue::GetObjectAsSByte(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::std::int8_t result;
    std::uint8_t resultIsValid = CallGetObjectAsSByte_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsByte_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::uint8_t* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::std::uint8_t> CesiumMetadataValue::GetObjectAsByte(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::std::uint8_t result;
    std::uint8_t resultIsValid = CallGetObjectAsByte_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsInt16_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::int16_t* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::std::int16_t> CesiumMetadataValue::GetObjectAsInt16(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::std::int16_t result;
    std::uint8_t resultIsValid = CallGetObjectAsInt16_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsUInt16_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::uint16_t* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::std::uint16_t> CesiumMetadataValue::GetObjectAsUInt16(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::std::uint16_t result;
    std::uint8_t resultIsValid = CallGetObjectAsUInt16_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsInt32_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::int32_t* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::std::int32_t> CesiumMetadataValue::GetObjectAsInt32(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::std::int32_t result;
    std::uint8_t resultIsValid = CallGetObjectAsInt32_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsUInt32_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::uint32_t* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::std::uint32_t> CesiumMetadataValue::GetObjectAsUInt32(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::std::uint32_t result;
    std::uint8_t resultIsValid = CallGetObjectAsUInt32_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsInt64_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::int64_t* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::std::int64_t> CesiumMetadataValue::GetObjectAsInt64(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::std::int64_t result;
    std::uint8_t resultIsValid = CallGetObjectAsInt64_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsUInt64_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::uint64_t* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::std::uint64_t> CesiumMetadataValue::GetObjectAsUInt64(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::std::uint64_t result;
    std::uint8_t resultIsValid = CallGetObjectAsUInt64_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, float* pReturnValue, void** reinteropException) = nullptr;


::std::optional<float> CesiumMetadataValue::GetObjectAsFloat(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    float result;
    std::uint8_t resultIsValid = CallGetObjectAsFloat_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, double* pReturnValue, void** reinteropException) = nullptr;


::std::optional<double> CesiumMetadataValue::GetObjectAsDouble(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    double result;
    std::uint8_t resultIsValid = CallGetObjectAsDouble_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntVec2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumIntVec2> CesiumMetadataValue::GetObjectAsCesiumIntVec2(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumIntVec2 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumIntVec2_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntVec3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumIntVec3> CesiumMetadataValue::GetObjectAsCesiumIntVec3(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumIntVec3 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumIntVec3_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntVec4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumIntVec4> CesiumMetadataValue::GetObjectAsCesiumIntVec4(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumIntVec4 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumIntVec4_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintVec2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumUintVec2> CesiumMetadataValue::GetObjectAsCesiumUintVec2(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumUintVec2 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumUintVec2_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintVec3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumUintVec3> CesiumMetadataValue::GetObjectAsCesiumUintVec3(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumUintVec3 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumUintVec3_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintVec4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumUintVec4> CesiumMetadataValue::GetObjectAsCesiumUintVec4(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumUintVec4 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumUintVec4_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float2* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::float2> CesiumMetadataValue::GetObjectAsFloat2(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float2 result;
    std::uint8_t resultIsValid = CallGetObjectAsFloat2_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float3* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::float3> CesiumMetadataValue::GetObjectAsFloat3(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float3 result;
    std::uint8_t resultIsValid = CallGetObjectAsFloat3_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float4* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::float4> CesiumMetadataValue::GetObjectAsFloat4(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float4 result;
    std::uint8_t resultIsValid = CallGetObjectAsFloat4_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double2* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::double2> CesiumMetadataValue::GetObjectAsDouble2(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double2 result;
    std::uint8_t resultIsValid = CallGetObjectAsDouble2_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::double3> CesiumMetadataValue::GetObjectAsDouble3(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double3 result;
    std::uint8_t resultIsValid = CallGetObjectAsDouble3_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double4* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::double4> CesiumMetadataValue::GetObjectAsDouble4(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double4 result;
    std::uint8_t resultIsValid = CallGetObjectAsDouble4_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntMat2x2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntMat2x2* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumIntMat2x2> CesiumMetadataValue::GetObjectAsCesiumIntMat2x2(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumIntMat2x2 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumIntMat2x2_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntMat3x3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntMat3x3* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumIntMat3x3> CesiumMetadataValue::GetObjectAsCesiumIntMat3x3(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumIntMat3x3 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumIntMat3x3_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumIntMat4x4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntMat4x4* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumIntMat4x4> CesiumMetadataValue::GetObjectAsCesiumIntMat4x4(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumIntMat4x4 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumIntMat4x4_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintMat2x2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintMat2x2* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumUintMat2x2> CesiumMetadataValue::GetObjectAsCesiumUintMat2x2(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumUintMat2x2 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumUintMat2x2_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintMat3x3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintMat3x3* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumUintMat3x3> CesiumMetadataValue::GetObjectAsCesiumUintMat3x3(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumUintMat3x3 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumUintMat3x3_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsCesiumUintMat4x4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintMat4x4* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::CesiumForUnity::CesiumUintMat4x4> CesiumMetadataValue::GetObjectAsCesiumUintMat4x4(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumUintMat4x4 result;
    std::uint8_t resultIsValid = CallGetObjectAsCesiumUintMat4x4_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat2x2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float2x2* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::float2x2> CesiumMetadataValue::GetObjectAsFloat2x2(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float2x2 result;
    std::uint8_t resultIsValid = CallGetObjectAsFloat2x2_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat3x3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float3x3* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::float3x3> CesiumMetadataValue::GetObjectAsFloat3x3(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float3x3 result;
    std::uint8_t resultIsValid = CallGetObjectAsFloat3x3_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsFloat4x4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float4x4* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::float4x4> CesiumMetadataValue::GetObjectAsFloat4x4(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float4x4 result;
    std::uint8_t resultIsValid = CallGetObjectAsFloat4x4_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble2x2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double2x2* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::double2x2> CesiumMetadataValue::GetObjectAsDouble2x2(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double2x2 result;
    std::uint8_t resultIsValid = CallGetObjectAsDouble2x2_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble3x3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double3x3* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::double3x3> CesiumMetadataValue::GetObjectAsDouble3x3(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double3x3 result;
    std::uint8_t resultIsValid = CallGetObjectAsDouble3x3_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsDouble4x4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException) = nullptr;


::std::optional<::DotNet::Unity::Mathematics::double4x4> CesiumMetadataValue::GetObjectAsDouble4x4(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double4x4 result;
    std::uint8_t resultIsValid = CallGetObjectAsDouble4x4_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return resultIsValid ? std::make_optional(std::move(result)) : std::nullopt;
}


void* (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetObjectAsString_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, void** reinteropException) = nullptr;


::DotNet::System::String CesiumMetadataValue::GetObjectAsString(const ::DotNet::System::Object& inObject) {
    void* reinteropException = nullptr;
    auto result = CallGetObjectAsString_AtRYgGwV_m_laH7E6OJuzQ(inObject.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetBoolean_8644xplB2__fgXE67sxDhig)(void* thiz, ::std::uint8_t defaultValue, void** reinteropException) = nullptr;


bool CesiumMetadataValue::GetBoolean(bool defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetBoolean_8644xplB2__fgXE67sxDhig((*this).GetHandle().GetRaw(), defaultValue ? 1 : 0, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


::std::int8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetSByte_u__Z7K16N77kyh7TEGfcD6w)(void* thiz, ::std::int8_t defaultValue, void** reinteropException) = nullptr;


::std::int8_t CesiumMetadataValue::GetSByte(::std::int8_t defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetSByte_u__Z7K16N77kyh7TEGfcD6w((*this).GetHandle().GetRaw(), defaultValue, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint8_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetByte_bGdPWSKS_QzGTQdjd0YUfg)(void* thiz, ::std::uint8_t defaultValue, void** reinteropException) = nullptr;


::std::uint8_t CesiumMetadataValue::GetByte(::std::uint8_t defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetByte_bGdPWSKS_QzGTQdjd0YUfg((*this).GetHandle().GetRaw(), defaultValue, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int16_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetInt16_WvwSboUzc5ebxbHqu1PVQQ)(void* thiz, ::std::int16_t defaultValue, void** reinteropException) = nullptr;


::std::int16_t CesiumMetadataValue::GetInt16(::std::int16_t defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetInt16_WvwSboUzc5ebxbHqu1PVQQ((*this).GetHandle().GetRaw(), defaultValue, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint16_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetUInt16_BrHiKvcj_xRGpq___J3u__uQ)(void* thiz, ::std::uint16_t defaultValue, void** reinteropException) = nullptr;


::std::uint16_t CesiumMetadataValue::GetUInt16(::std::uint16_t defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetUInt16_BrHiKvcj_xRGpq___J3u__uQ((*this).GetHandle().GetRaw(), defaultValue, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int32_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetInt32_998gVIdn2_HYywxhSBOEWQ)(void* thiz, ::std::int32_t defaultValue, void** reinteropException) = nullptr;


::std::int32_t CesiumMetadataValue::GetInt32(::std::int32_t defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetInt32_998gVIdn2_HYywxhSBOEWQ((*this).GetHandle().GetRaw(), defaultValue, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint32_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetUInt32_vwiv7sse1kaHlVcmj3cmhA)(void* thiz, ::std::uint32_t defaultValue, void** reinteropException) = nullptr;


::std::uint32_t CesiumMetadataValue::GetUInt32(::std::uint32_t defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetUInt32_vwiv7sse1kaHlVcmj3cmhA((*this).GetHandle().GetRaw(), defaultValue, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetInt64_QUJbZD3LR0PMPHpOtGaL8A)(void* thiz, ::std::int64_t defaultValue, void** reinteropException) = nullptr;


::std::int64_t CesiumMetadataValue::GetInt64(::std::int64_t defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetInt64_QUJbZD3LR0PMPHpOtGaL8A((*this).GetHandle().GetRaw(), defaultValue, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint64_t (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetUInt64_IoU0bf6YAddSM0L1le5WZw)(void* thiz, ::std::uint64_t defaultValue, void** reinteropException) = nullptr;


::std::uint64_t CesiumMetadataValue::GetUInt64(::std::uint64_t defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetUInt64_IoU0bf6YAddSM0L1le5WZw((*this).GetHandle().GetRaw(), defaultValue, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


float (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetFloat_vH9G7A1WLTqjf5CZMDNGIg)(void* thiz, float defaultValue, void** reinteropException) = nullptr;


float CesiumMetadataValue::GetFloat(float defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetFloat_vH9G7A1WLTqjf5CZMDNGIg((*this).GetHandle().GetRaw(), defaultValue, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


double (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetDouble_N2mzpgM1De7RfBi9SEVd3g)(void* thiz, double defaultValue, void** reinteropException) = nullptr;


double CesiumMetadataValue::GetDouble(double defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetDouble_N2mzpgM1De7RfBi9SEVd3g((*this).GetHandle().GetRaw(), defaultValue, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetString_lQJ2w4ouvMx3GLqlEgEyGg)(void* thiz, void* defaultValue, void** reinteropException) = nullptr;


::DotNet::System::String CesiumMetadataValue::GetString(const ::DotNet::System::String& defaultValue) const {
    void* reinteropException = nullptr;
    auto result = CallGetString_lQJ2w4ouvMx3GLqlEgEyGg((*this).GetHandle().GetRaw(), defaultValue.GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(result));
}


void* (*DotNet::CesiumForUnity::CesiumMetadataValue::CallGetArray_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumPropertyArray CesiumMetadataValue::GetArray() const {
    void* reinteropException = nullptr;
    auto result = CallGetArray_1B2M2Y8AsgTpgAmY7PhCfg((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::CesiumForUnity::CesiumPropertyArray(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::CesiumForUnity

extern "C" {

#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToBoolean(void* value, ::std::uint8_t defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToBoolean(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), !!defaultValue);
    return result ? 1 : 0;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int8_t DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToSByte(void* value, ::std::int8_t defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToSByte(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint8_t DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToByte(void* value, ::std::uint8_t defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToByte(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint8_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint8_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint8_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int16_t DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToInt16(void* value, ::std::int16_t defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToInt16(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int16_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int16_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int16_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint16_t DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToUInt16(void* value, ::std::uint16_t defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToUInt16(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint16_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint16_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint16_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int32_t DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToInt32(void* value, ::std::int32_t defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToInt32(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int32_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int32_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int32_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint32_t DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToUInt32(void* value, ::std::uint32_t defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToUInt32(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint32_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint32_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint32_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::int64_t DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToInt64(void* value, ::std::int64_t defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToInt64(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::int64_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::int64_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::int64_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
::std::uint64_t DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToUInt64(void* value, ::std::uint64_t defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToUInt64(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return ::std::uint64_t();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return ::std::uint64_t();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return ::std::uint64_t();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
float DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToFloat(void* value, float defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToFloat(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return float();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return float();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return float();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
double DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToDouble(void* value, double defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToDouble(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), defaultValue);
    return result;
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return double();
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return double();
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return double();
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToInt2(void* value, const ::DotNet::Unity::Mathematics::int2* defaultValue, ::DotNet::Unity::Mathematics::int2* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToInt2(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToUInt2(void* value, const ::DotNet::Unity::Mathematics::uint2* defaultValue, ::DotNet::Unity::Mathematics::uint2* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToUInt2(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToFloat2(void* value, const ::DotNet::Unity::Mathematics::float2* defaultValue, ::DotNet::Unity::Mathematics::float2* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToFloat2(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToDouble2(void* value, const ::DotNet::Unity::Mathematics::double2* defaultValue, ::DotNet::Unity::Mathematics::double2* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToDouble2(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToInt3(void* value, const ::DotNet::Unity::Mathematics::int3* defaultValue, ::DotNet::Unity::Mathematics::int3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToInt3(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToUInt3(void* value, const ::DotNet::Unity::Mathematics::uint3* defaultValue, ::DotNet::Unity::Mathematics::uint3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToUInt3(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToFloat3(void* value, const ::DotNet::Unity::Mathematics::float3* defaultValue, ::DotNet::Unity::Mathematics::float3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToFloat3(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToDouble3(void* value, const ::DotNet::Unity::Mathematics::double3* defaultValue, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToDouble3(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToInt4(void* value, const ::DotNet::Unity::Mathematics::int4* defaultValue, ::DotNet::Unity::Mathematics::int4* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToInt4(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToUInt4(void* value, const ::DotNet::Unity::Mathematics::uint4* defaultValue, ::DotNet::Unity::Mathematics::uint4* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToUInt4(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToFloat4(void* value, const ::DotNet::Unity::Mathematics::float4* defaultValue, ::DotNet::Unity::Mathematics::float4* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToFloat4(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToDouble4(void* value, const ::DotNet::Unity::Mathematics::double4* defaultValue, ::DotNet::Unity::Mathematics::double4* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToDouble4(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToInt2x2(void* value, const ::DotNet::Unity::Mathematics::int2x2* defaultValue, ::DotNet::Unity::Mathematics::int2x2* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToInt2x2(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToUInt2x2(void* value, const ::DotNet::Unity::Mathematics::uint2x2* defaultValue, ::DotNet::Unity::Mathematics::uint2x2* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToUInt2x2(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToFloat2x2(void* value, const ::DotNet::Unity::Mathematics::float2x2* defaultValue, ::DotNet::Unity::Mathematics::float2x2* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToFloat2x2(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToDouble2x2(void* value, const ::DotNet::Unity::Mathematics::double2x2* defaultValue, ::DotNet::Unity::Mathematics::double2x2* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToDouble2x2(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToInt3x3(void* value, const ::DotNet::Unity::Mathematics::int3x3* defaultValue, ::DotNet::Unity::Mathematics::int3x3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToInt3x3(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToUInt3x3(void* value, const ::DotNet::Unity::Mathematics::uint3x3* defaultValue, ::DotNet::Unity::Mathematics::uint3x3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToUInt3x3(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToFloat3x3(void* value, const ::DotNet::Unity::Mathematics::float3x3* defaultValue, ::DotNet::Unity::Mathematics::float3x3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToFloat3x3(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToDouble3x3(void* value, const ::DotNet::Unity::Mathematics::double3x3* defaultValue, ::DotNet::Unity::Mathematics::double3x3* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToDouble3x3(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToInt4x4(void* value, const ::DotNet::Unity::Mathematics::int4x4* defaultValue, ::DotNet::Unity::Mathematics::int4x4* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToInt4x4(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToUInt4x4(void* value, const ::DotNet::Unity::Mathematics::uint4x4* defaultValue, ::DotNet::Unity::Mathematics::uint4x4* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToUInt4x4(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToFloat4x4(void* value, const ::DotNet::Unity::Mathematics::float4x4* defaultValue, ::DotNet::Unity::Mathematics::float4x4* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToFloat4x4(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToDouble4x4(void* value, const ::DotNet::Unity::Mathematics::double4x4* defaultValue, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToDouble4x4(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), *defaultValue);
    *pReturnValue = std::move(result);
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    
  }                   
}
#if defined(_WIN32)
__declspec(dllexport)
#endif
void* DotNet_CesiumForUnity_CesiumMetadataValue_ConvertToString(void* value, void* defaultValue, void** reinteropException) {
  try {
    
    auto result = CesiumForUnityNative::CesiumMetadataValueImpl::ConvertToString(::DotNet::CesiumForUnity::CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle(value)), ::DotNet::System::String(::DotNet::Reinterop::ObjectHandle(defaultValue)));
    return result.GetHandle().Release();
  } catch (::DotNet::Reinterop::ReinteropNativeException& e) {
    *reinteropException = ::DotNet::Reinterop::ObjectHandle(e.GetDotNetException().GetHandle()).Release();
    return nullptr;
  } catch (std::exception& e) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String(e.what())).GetHandle().Release();
    return nullptr;
  } catch (...) {
    *reinteropException = ::DotNet::Reinterop::ReinteropException(::DotNet::System::String("An unknown native exception occurred.")).GetHandle().Release();
    return nullptr;
  }                   
}

} // extern "C"

