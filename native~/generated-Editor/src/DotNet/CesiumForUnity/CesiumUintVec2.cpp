#include <DotNet/CesiumForUnity/CesiumUintVec2.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec2;
}

namespace DotNet::CesiumForUnity {

void (*CesiumUintVec2::Construct_ooy5yIq__mBEC6X6EtGX5Ow)(::std::uint8_t x, ::std::uint8_t y, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec2 CesiumUintVec2::Construct(::std::uint8_t x, ::std::uint8_t y)
{
    void* reinteropException = nullptr;
    CesiumUintVec2 result;
    Construct_ooy5yIq__mBEC6X6EtGX5Ow(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumUintVec2::Construct_XhEMD4DBm1OQpJbAQjBMWw)(::std::uint16_t x, ::std::uint16_t y, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec2 CesiumUintVec2::Construct(::std::uint16_t x, ::std::uint16_t y)
{
    void* reinteropException = nullptr;
    CesiumUintVec2 result;
    Construct_XhEMD4DBm1OQpJbAQjBMWw(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumUintVec2::Construct_41DRfMZ91WmKUsGkzEnbPw)(::std::uint32_t x, ::std::uint32_t y, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec2 CesiumUintVec2::Construct(::std::uint32_t x, ::std::uint32_t y)
{
    void* reinteropException = nullptr;
    CesiumUintVec2 result;
    Construct_41DRfMZ91WmKUsGkzEnbPw(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumUintVec2::Construct_nrWljXjq__N5wiftR3c_JGg)(::std::uint64_t x, ::std::uint64_t y, ::DotNet::CesiumForUnity::CesiumUintVec2* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec2 CesiumUintVec2::Construct(::std::uint64_t x, ::std::uint64_t y)
{
    void* reinteropException = nullptr;
    CesiumUintVec2 result;
    Construct_nrWljXjq__N5wiftR3c_JGg(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint64_t (*DotNet::CesiumForUnity::CesiumUintVec2::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintVec2* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::std::uint64_t CesiumUintVec2::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


