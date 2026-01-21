#include <DotNet/CesiumForUnity/CesiumUintVec4.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec4;
}

namespace DotNet::CesiumForUnity {

void (*CesiumUintVec4::Construct_V8zlQY__7MR4_A1Ek6HBQqg)(::std::uint8_t x, ::std::uint8_t y, ::std::uint8_t z, ::std::uint8_t w, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec4 CesiumUintVec4::Construct(::std::uint8_t x, ::std::uint8_t y, ::std::uint8_t z, ::std::uint8_t w)
{
    void* reinteropException = nullptr;
    CesiumUintVec4 result;
    Construct_V8zlQY__7MR4_A1Ek6HBQqg(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumUintVec4::Construct_yp__VrxlOcxUXq2RwGv8mXw)(::std::uint16_t x, ::std::uint16_t y, ::std::uint16_t z, ::std::uint16_t w, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec4 CesiumUintVec4::Construct(::std::uint16_t x, ::std::uint16_t y, ::std::uint16_t z, ::std::uint16_t w)
{
    void* reinteropException = nullptr;
    CesiumUintVec4 result;
    Construct_yp__VrxlOcxUXq2RwGv8mXw(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumUintVec4::Construct_cx5C8OyRaFgckdYoG5u6cw)(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::std::uint32_t w, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec4 CesiumUintVec4::Construct(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::std::uint32_t w)
{
    void* reinteropException = nullptr;
    CesiumUintVec4 result;
    Construct_cx5C8OyRaFgckdYoG5u6cw(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumUintVec4::Construct_eKggYQNxOSW0_H_SNc53xA)(::std::uint64_t x, ::std::uint64_t y, ::std::uint64_t z, ::std::uint64_t w, ::DotNet::CesiumForUnity::CesiumUintVec4* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec4 CesiumUintVec4::Construct(::std::uint64_t x, ::std::uint64_t y, ::std::uint64_t z, ::std::uint64_t w)
{
    void* reinteropException = nullptr;
    CesiumUintVec4 result;
    Construct_eKggYQNxOSW0_H_SNc53xA(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint64_t (*DotNet::CesiumForUnity::CesiumUintVec4::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintVec4* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::std::uint64_t CesiumUintVec4::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


