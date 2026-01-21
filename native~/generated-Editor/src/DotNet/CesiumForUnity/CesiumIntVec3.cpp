#include <DotNet/CesiumForUnity/CesiumIntVec3.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec3;
}

namespace DotNet::CesiumForUnity {

void (*CesiumIntVec3::Construct_luE9S3oIPaPU1lLegMPAPA)(::std::int8_t x, ::std::int8_t y, ::std::int8_t z, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec3 CesiumIntVec3::Construct(::std::int8_t x, ::std::int8_t y, ::std::int8_t z)
{
    void* reinteropException = nullptr;
    CesiumIntVec3 result;
    Construct_luE9S3oIPaPU1lLegMPAPA(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumIntVec3::Construct_cAgWTHR8SgDZQ7UniQULbg)(::std::int16_t x, ::std::int16_t y, ::std::int16_t z, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec3 CesiumIntVec3::Construct(::std::int16_t x, ::std::int16_t y, ::std::int16_t z)
{
    void* reinteropException = nullptr;
    CesiumIntVec3 result;
    Construct_cAgWTHR8SgDZQ7UniQULbg(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumIntVec3::Construct_2lzDmp63Mfw__oFMy0HdgWw)(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec3 CesiumIntVec3::Construct(::std::int32_t x, ::std::int32_t y, ::std::int32_t z)
{
    void* reinteropException = nullptr;
    CesiumIntVec3 result;
    Construct_2lzDmp63Mfw__oFMy0HdgWw(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumIntVec3::Construct_8bShh4o97BtgzpoxMAXY5g)(::std::int64_t x, ::std::int64_t y, ::std::int64_t z, ::DotNet::CesiumForUnity::CesiumIntVec3* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec3 CesiumIntVec3::Construct(::std::int64_t x, ::std::int64_t y, ::std::int64_t z)
{
    void* reinteropException = nullptr;
    CesiumIntVec3 result;
    Construct_8bShh4o97BtgzpoxMAXY5g(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumIntVec3::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntVec3* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::std::int64_t CesiumIntVec3::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


