#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <optional>
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

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::CesiumForUnity {
struct CesiumMetadataValueType;
}
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
namespace DotNet::System {
class String;
}
namespace DotNet::CesiumForUnity {
class CesiumPropertyArray;
}

namespace DotNet::CesiumForUnity {

class CesiumMetadataValue {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumMetadataValue(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumMetadataValue(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: CesiumMetadataValue();
  public: operator ::DotNet::System::Object() const;
  private: static void (*Property_get_valueType)(void* thiz, ::DotNet::CesiumForUnity::CesiumMetadataValueType* pReturnValue, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumMetadataValueType valueType() const;
  private: static void* (*Property_get_objectValue)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Object objectValue() const;
  private: static void (*Property_set_objectValue)(void* thiz, void* value, void** reinteropException);
  public: void objectValue(const ::DotNet::System::Object& value) const;
  private: static void (*CallSetObjectValue_K2SuSn7V3nS18YMZRRK2Lw)(void* thiz, ::std::uint8_t input, void** reinteropException);
  public: void SetObjectValue(bool input) const;
  private: static void (*CallSetObjectValue___hk7qZfa8rr3GOj5LB___2w)(void* thiz, ::std::int8_t input, void** reinteropException);
  public: void SetObjectValue(::std::int8_t input) const;
  private: static void (*CallSetObjectValue_AOHrSvkQjQG6kWS8yHSsZg)(void* thiz, ::std::uint8_t input, void** reinteropException);
  public: void SetObjectValue(::std::uint8_t input) const;
  private: static void (*CallSetObjectValue_GOjK0KanRT1fe9j2Ayd54A)(void* thiz, ::std::int16_t input, void** reinteropException);
  public: void SetObjectValue(::std::int16_t input) const;
  private: static void (*CallSetObjectValue_J5rOnxox49GXbyekWYJkRg)(void* thiz, ::std::uint16_t input, void** reinteropException);
  public: void SetObjectValue(::std::uint16_t input) const;
  private: static void (*CallSetObjectValue_hQOJfT5zVEav_dYgl__2qDA)(void* thiz, ::std::int32_t input, void** reinteropException);
  public: void SetObjectValue(::std::int32_t input) const;
  private: static void (*CallSetObjectValue_dwf4e0_X4__X16sg27oT_HA)(void* thiz, ::std::uint32_t input, void** reinteropException);
  public: void SetObjectValue(::std::uint32_t input) const;
  private: static void (*CallSetObjectValue_FD9BTdwh6Rq_Uqnx3WcYzw)(void* thiz, ::std::int64_t input, void** reinteropException);
  public: void SetObjectValue(::std::int64_t input) const;
  private: static void (*CallSetObjectValue_qWiVKY8F7ND55zOj2iwazg)(void* thiz, ::std::uint64_t input, void** reinteropException);
  public: void SetObjectValue(::std::uint64_t input) const;
  private: static void (*CallSetObjectValue_t__W_mBs2JX7Isb90n6lv8A)(void* thiz, float input, void** reinteropException);
  public: void SetObjectValue(float input) const;
  private: static void (*CallSetObjectValue_2x5EigY7rzmfbErsKTGuwA)(void* thiz, double input, void** reinteropException);
  public: void SetObjectValue(double input) const;
  private: static void (*CallSetObjectValue_1WBg__LUjCHSaTnVxWpW9hg)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntVec2* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntVec2& input) const;
  private: static void (*CallSetObjectValue_0MPHAdrwN6Tw6ckL78VuSw)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntVec3* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntVec3& input) const;
  private: static void (*CallSetObjectValue_SJOlUbxBoNfhxbRZHSyjCA)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntVec4* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntVec4& input) const;
  private: static void (*CallSetObjectValue_6IVxYw6_3__T__eM__j5WVcGA)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintVec2* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintVec2& input) const;
  private: static void (*CallSetObjectValue_AZB45d2Wd0Dhi64vRZNcpQ)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintVec3* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintVec3& input) const;
  private: static void (*CallSetObjectValue_CxH9s__3LeVVRneWxCIMJeQ)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintVec4* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintVec4& input) const;
  private: static void (*CallSetObjectValue_rf6L9ndiTJQiNeSLGMcN3g)(void* thiz, const ::DotNet::Unity::Mathematics::float2* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::float2& input) const;
  private: static void (*CallSetObjectValue_9Xqzdq684P0z1H__FquaaBA)(void* thiz, const ::DotNet::Unity::Mathematics::float3* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::float3& input) const;
  private: static void (*CallSetObjectValue_VPZKsFl98vDFige9cNHc9g)(void* thiz, const ::DotNet::Unity::Mathematics::float4* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::float4& input) const;
  private: static void (*CallSetObjectValue___WBWu0KVcnlBoRHTz18iQg)(void* thiz, const ::DotNet::Unity::Mathematics::double2* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::double2& input) const;
  private: static void (*CallSetObjectValue_1dZuiOwXjOp7XXu7VmYFKg)(void* thiz, const ::DotNet::Unity::Mathematics::double3* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::double3& input) const;
  private: static void (*CallSetObjectValue_lWaGb__IpQLOSjzXG2ChwiQ)(void* thiz, const ::DotNet::Unity::Mathematics::double4* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::double4& input) const;
  private: static void (*CallSetObjectValue_KdIbPno6dUQIzkDlllX7cQ)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntMat2x2* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntMat2x2& input) const;
  private: static void (*CallSetObjectValue_LfJM7X33EQGf4jiLbGxqWw)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntMat3x3* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntMat3x3& input) const;
  private: static void (*CallSetObjectValue_tgJ__I0QxIjujzxx4laL3bA)(void* thiz, const ::DotNet::CesiumForUnity::CesiumIntMat4x4* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumIntMat4x4& input) const;
  private: static void (*CallSetObjectValue_jpn00ft20c7Tvsbl6__LFPg)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintMat2x2* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintMat2x2& input) const;
  private: static void (*CallSetObjectValue_WfkO9L_m4izzalpvtro06A)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintMat3x3* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintMat3x3& input) const;
  private: static void (*CallSetObjectValue_OHiI21kQ_keDg54_OLHJFA)(void* thiz, const ::DotNet::CesiumForUnity::CesiumUintMat4x4* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumUintMat4x4& input) const;
  private: static void (*CallSetObjectValue_p6Nq4_g8K2hv1dGlLZFq4A)(void* thiz, const ::DotNet::Unity::Mathematics::float2x2* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::float2x2& input) const;
  private: static void (*CallSetObjectValue__dwRw4SrC5dQwg9WXOVCWA)(void* thiz, const ::DotNet::Unity::Mathematics::float3x3* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::float3x3& input) const;
  private: static void (*CallSetObjectValue_YhLOr6l38fDvTI1UYnZdTg)(void* thiz, const ::DotNet::Unity::Mathematics::float4x4* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::float4x4& input) const;
  private: static void (*CallSetObjectValue_t4X__QJT6bJG22Rlb0EUSGg)(void* thiz, const ::DotNet::Unity::Mathematics::double2x2* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::double2x2& input) const;
  private: static void (*CallSetObjectValue_3NklrXK7mSsrFiAUMUIpHw)(void* thiz, const ::DotNet::Unity::Mathematics::double3x3* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::double3x3& input) const;
  private: static void (*CallSetObjectValue_cbZNG6837P_AD_Fyz7orDg)(void* thiz, const ::DotNet::Unity::Mathematics::double4x4* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::Unity::Mathematics::double4x4& input) const;
  private: static void (*CallSetObjectValue_OekvF3gFc1nGTHuKfXsZ3g)(void* thiz, void* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::System::String& input) const;
  private: static void (*CallSetObjectValue_wnAsp0qKwHuRGJ3ZIPvzeA)(void* thiz, void* input, void** reinteropException);
  public: void SetObjectValue(const ::DotNet::CesiumForUnity::CesiumPropertyArray& input) const;
  private: static ::std::uint8_t (*CallGetObjectAsBoolean_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, bool* pReturnValue, void** reinteropException);
  public: static ::std::optional<bool> GetObjectAsBoolean(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsSByte_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::int8_t* pReturnValue, void** reinteropException);
  public: static ::std::optional<::std::int8_t> GetObjectAsSByte(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsByte_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::uint8_t* pReturnValue, void** reinteropException);
  public: static ::std::optional<::std::uint8_t> GetObjectAsByte(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsInt16_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::int16_t* pReturnValue, void** reinteropException);
  public: static ::std::optional<::std::int16_t> GetObjectAsInt16(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsUInt16_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::uint16_t* pReturnValue, void** reinteropException);
  public: static ::std::optional<::std::uint16_t> GetObjectAsUInt16(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsInt32_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::int32_t* pReturnValue, void** reinteropException);
  public: static ::std::optional<::std::int32_t> GetObjectAsInt32(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsUInt32_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::uint32_t* pReturnValue, void** reinteropException);
  public: static ::std::optional<::std::uint32_t> GetObjectAsUInt32(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsInt64_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::int64_t* pReturnValue, void** reinteropException);
  public: static ::std::optional<::std::int64_t> GetObjectAsInt64(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsUInt64_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::std::uint64_t* pReturnValue, void** reinteropException);
  public: static ::std::optional<::std::uint64_t> GetObjectAsUInt64(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsFloat_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, float* pReturnValue, void** reinteropException);
  public: static ::std::optional<float> GetObjectAsFloat(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsDouble_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, double* pReturnValue, void** reinteropException);
  public: static ::std::optional<double> GetObjectAsDouble(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumIntVec2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumIntVec2> GetObjectAsCesiumIntVec2(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumIntVec3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumIntVec3> GetObjectAsCesiumIntVec3(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumIntVec4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumIntVec4> GetObjectAsCesiumIntVec4(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumUintVec2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumUintVec2> GetObjectAsCesiumUintVec2(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumUintVec3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumUintVec3> GetObjectAsCesiumUintVec3(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumUintVec4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumUintVec4> GetObjectAsCesiumUintVec4(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsFloat2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float2* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::float2> GetObjectAsFloat2(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsFloat3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float3* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::float3> GetObjectAsFloat3(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsFloat4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float4* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::float4> GetObjectAsFloat4(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsDouble2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double2* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::double2> GetObjectAsDouble2(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsDouble3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::double3> GetObjectAsDouble3(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsDouble4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double4* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::double4> GetObjectAsDouble4(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumIntMat2x2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntMat2x2* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumIntMat2x2> GetObjectAsCesiumIntMat2x2(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumIntMat3x3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntMat3x3* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumIntMat3x3> GetObjectAsCesiumIntMat3x3(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumIntMat4x4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumIntMat4x4* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumIntMat4x4> GetObjectAsCesiumIntMat4x4(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumUintMat2x2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintMat2x2* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumUintMat2x2> GetObjectAsCesiumUintMat2x2(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumUintMat3x3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintMat3x3* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumUintMat3x3> GetObjectAsCesiumUintMat3x3(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsCesiumUintMat4x4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::CesiumForUnity::CesiumUintMat4x4* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::CesiumForUnity::CesiumUintMat4x4> GetObjectAsCesiumUintMat4x4(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsFloat2x2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float2x2* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::float2x2> GetObjectAsFloat2x2(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsFloat3x3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float3x3* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::float3x3> GetObjectAsFloat3x3(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsFloat4x4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::float4x4* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::float4x4> GetObjectAsFloat4x4(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsDouble2x2_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double2x2* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::double2x2> GetObjectAsDouble2x2(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsDouble3x3_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double3x3* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::double3x3> GetObjectAsDouble3x3(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetObjectAsDouble4x4_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException);
  public: static ::std::optional<::DotNet::Unity::Mathematics::double4x4> GetObjectAsDouble4x4(const ::DotNet::System::Object& inObject);
  private: static void* (*CallGetObjectAsString_AtRYgGwV_m_laH7E6OJuzQ)(void* inObject, void** reinteropException);
  public: static ::DotNet::System::String GetObjectAsString(const ::DotNet::System::Object& inObject);
  private: static ::std::uint8_t (*CallGetBoolean_8644xplB2__fgXE67sxDhig)(void* thiz, ::std::uint8_t defaultValue, void** reinteropException);
  public: bool GetBoolean(bool defaultValue) const;
  private: static ::std::int8_t (*CallGetSByte_u__Z7K16N77kyh7TEGfcD6w)(void* thiz, ::std::int8_t defaultValue, void** reinteropException);
  public: ::std::int8_t GetSByte(::std::int8_t defaultValue) const;
  private: static ::std::uint8_t (*CallGetByte_bGdPWSKS_QzGTQdjd0YUfg)(void* thiz, ::std::uint8_t defaultValue, void** reinteropException);
  public: ::std::uint8_t GetByte(::std::uint8_t defaultValue) const;
  private: static ::std::int16_t (*CallGetInt16_WvwSboUzc5ebxbHqu1PVQQ)(void* thiz, ::std::int16_t defaultValue, void** reinteropException);
  public: ::std::int16_t GetInt16(::std::int16_t defaultValue) const;
  private: static ::std::uint16_t (*CallGetUInt16_BrHiKvcj_xRGpq___J3u__uQ)(void* thiz, ::std::uint16_t defaultValue, void** reinteropException);
  public: ::std::uint16_t GetUInt16(::std::uint16_t defaultValue) const;
  private: static ::std::int32_t (*CallGetInt32_998gVIdn2_HYywxhSBOEWQ)(void* thiz, ::std::int32_t defaultValue, void** reinteropException);
  public: ::std::int32_t GetInt32(::std::int32_t defaultValue) const;
  private: static ::std::uint32_t (*CallGetUInt32_vwiv7sse1kaHlVcmj3cmhA)(void* thiz, ::std::uint32_t defaultValue, void** reinteropException);
  public: ::std::uint32_t GetUInt32(::std::uint32_t defaultValue) const;
  private: static ::std::int64_t (*CallGetInt64_QUJbZD3LR0PMPHpOtGaL8A)(void* thiz, ::std::int64_t defaultValue, void** reinteropException);
  public: ::std::int64_t GetInt64(::std::int64_t defaultValue) const;
  private: static ::std::uint64_t (*CallGetUInt64_IoU0bf6YAddSM0L1le5WZw)(void* thiz, ::std::uint64_t defaultValue, void** reinteropException);
  public: ::std::uint64_t GetUInt64(::std::uint64_t defaultValue) const;
  private: static float (*CallGetFloat_vH9G7A1WLTqjf5CZMDNGIg)(void* thiz, float defaultValue, void** reinteropException);
  public: float GetFloat(float defaultValue) const;
  private: static double (*CallGetDouble_N2mzpgM1De7RfBi9SEVd3g)(void* thiz, double defaultValue, void** reinteropException);
  public: double GetDouble(double defaultValue) const;
  private: static void* (*CallGetString_lQJ2w4ouvMx3GLqlEgEyGg)(void* thiz, void* defaultValue, void** reinteropException);
  public: ::DotNet::System::String GetString(const ::DotNet::System::String& defaultValue) const;
  private: static void* (*CallGetArray_1B2M2Y8AsgTpgAmY7PhCfg)(void* thiz, void** reinteropException);
  public: ::DotNet::CesiumForUnity::CesiumPropertyArray GetArray() const;
};

} // namespace DotNet::CesiumForUnity


