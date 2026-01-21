#include <DotNet/CesiumForUnity/CesiumIntVec2.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec2;
}

namespace DotNet::CesiumForUnity {

void (*CesiumIntVec2::Construct_iC__gCkOnQfbe6NMbdvLiGg)(::std::int8_t x, ::std::int8_t y, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec2 CesiumIntVec2::Construct(::std::int8_t x, ::std::int8_t y)
{
    void* reinteropException = nullptr;
    CesiumIntVec2 result;
    Construct_iC__gCkOnQfbe6NMbdvLiGg(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumIntVec2::Construct_dZv0kAenH9__iFQ8xBVdqfQ)(::std::int16_t x, ::std::int16_t y, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec2 CesiumIntVec2::Construct(::std::int16_t x, ::std::int16_t y)
{
    void* reinteropException = nullptr;
    CesiumIntVec2 result;
    Construct_dZv0kAenH9__iFQ8xBVdqfQ(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumIntVec2::Construct_CSSfw_WOk6__K5__v8pO4eLw)(::std::int32_t x, ::std::int32_t y, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec2 CesiumIntVec2::Construct(::std::int32_t x, ::std::int32_t y)
{
    void* reinteropException = nullptr;
    CesiumIntVec2 result;
    Construct_CSSfw_WOk6__K5__v8pO4eLw(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*CesiumIntVec2::Construct_tS0EQwQ6_Z2EVvmR2x05Hg)(::std::int64_t x, ::std::int64_t y, ::DotNet::CesiumForUnity::CesiumIntVec2* pReturnValue, void** reinteropException) = nullptr;


CesiumIntVec2 CesiumIntVec2::Construct(::std::int64_t x, ::std::int64_t y)
{
    void* reinteropException = nullptr;
    CesiumIntVec2 result;
    Construct_tS0EQwQ6_Z2EVvmR2x05Hg(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


::std::int64_t (*DotNet::CesiumForUnity::CesiumIntVec2::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntVec2* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


::std::int64_t CesiumIntVec2::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


