#include <DotNet/CesiumForUnity/CesiumUintVec3.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::CesiumForUnity {
struct CesiumUintVec3;
}

namespace DotNet::CesiumForUnity {

void (*CesiumUintVec3::Construct_jH1j0POYh80kGurO6bbg6w)(::std::uint8_t x, ::std::uint8_t y, ::std::uint8_t z, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec3 CesiumUintVec3::Construct(::std::uint8_t x, ::std::uint8_t y, ::std::uint8_t z)
{
    void* reinteropException = nullptr;
    CesiumUintVec3 result;
    Construct_jH1j0POYh80kGurO6bbg6w(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumUintVec3::Construct_r71YnkpCpNgMBAJTUEeKlg)(::std::uint16_t x, ::std::uint16_t y, ::std::uint16_t z, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec3 CesiumUintVec3::Construct(::std::uint16_t x, ::std::uint16_t y, ::std::uint16_t z)
{
    void* reinteropException = nullptr;
    CesiumUintVec3 result;
    Construct_r71YnkpCpNgMBAJTUEeKlg(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumUintVec3::Construct_fwI58ky8hlqSzCrUJCqq4Q)(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec3 CesiumUintVec3::Construct(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z)
{
    void* reinteropException = nullptr;
    CesiumUintVec3 result;
    Construct_fwI58ky8hlqSzCrUJCqq4Q(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumUintVec3::Construct_ZbSqyVsWZtDI0Ryj__6S2Iw)(::std::uint64_t x, ::std::uint64_t y, ::std::uint64_t z, ::DotNet::CesiumForUnity::CesiumUintVec3* pReturnValue, void** reinteropException) = nullptr;


CesiumUintVec3 CesiumUintVec3::Construct(::std::uint64_t x, ::std::uint64_t y, ::std::uint64_t z)
{
    void* reinteropException = nullptr;
    CesiumUintVec3 result;
    Construct_ZbSqyVsWZtDI0Ryj__6S2Iw(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::uint64_t (*DotNet::CesiumForUnity::CesiumUintVec3::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumUintVec3* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::std::uint64_t CesiumUintVec3::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


