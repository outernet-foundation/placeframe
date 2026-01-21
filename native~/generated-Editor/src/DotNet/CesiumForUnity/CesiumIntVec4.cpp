#include <DotNet/CesiumForUnity/CesiumIntVec4.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec4;
}

namespace DotNet::CesiumForUnity {

void (*CesiumIntVec4::Construct__tGDX2UJ5ZtAXl4__zRN6Rg)(::std::int8_t x, ::std::int8_t y, ::std::int8_t z, ::std::int8_t w, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec4 CesiumIntVec4::Construct(::std::int8_t x, ::std::int8_t y, ::std::int8_t z, ::std::int8_t w)
{
    void* reinteropException = nullptr;
    CesiumIntVec4 result;
    Construct__tGDX2UJ5ZtAXl4__zRN6Rg(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumIntVec4::Construct_yhJRKUizUTWOe_SY6NdeKQ)(::std::int16_t x, ::std::int16_t y, ::std::int16_t z, ::std::int16_t w, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec4 CesiumIntVec4::Construct(::std::int16_t x, ::std::int16_t y, ::std::int16_t z, ::std::int16_t w)
{
    void* reinteropException = nullptr;
    CesiumIntVec4 result;
    Construct_yhJRKUizUTWOe_SY6NdeKQ(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumIntVec4::Construct_ima1GH0lko9R2DnR_aRPyw)(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::std::int32_t w, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec4 CesiumIntVec4::Construct(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::std::int32_t w)
{
    void* reinteropException = nullptr;
    CesiumIntVec4 result;
    Construct_ima1GH0lko9R2DnR_aRPyw(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumIntVec4::Construct_KoW6Dv__2RVyEhBpX4dwRww)(::std::int64_t x, ::std::int64_t y, ::std::int64_t z, ::std::int64_t w, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec4 CesiumIntVec4::Construct(::std::int64_t x, ::std::int64_t y, ::std::int64_t z, ::std::int64_t w)
{
    void* reinteropException = nullptr;
    CesiumIntVec4 result;
    Construct_KoW6Dv__2RVyEhBpX4dwRww(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumIntVec4::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntVec4* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::std::int64_t CesiumIntVec4::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


