#include <DotNet/CesiumForUnity/CesiumIntMat4x4.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumIntVec4.h>
#include <cstdint>

namespace DotNet::CesiumForUnity {
struct CesiumIntVec4;
}
namespace DotNet::CesiumForUnity {
struct CesiumIntMat4x4;
}

namespace DotNet::CesiumForUnity {

void (*CesiumIntMat4x4::Construct_1oaleqFQUQx5j2RbOSvw3w)(const ::DotNet::CesiumForUnity::CesiumIntVec4* v0, const ::DotNet::CesiumForUnity::CesiumIntVec4* v1, const ::DotNet::CesiumForUnity::CesiumIntVec4* v2, const ::DotNet::CesiumForUnity::CesiumIntVec4* v3, ::DotNet::CesiumForUnity::CesiumIntMat4x4* pReturnValue, void** reinteropException) = nullptr;


CesiumIntMat4x4 CesiumIntMat4x4::Construct(const ::DotNet::CesiumForUnity::CesiumIntVec4& v0, const ::DotNet::CesiumForUnity::CesiumIntVec4& v1, const ::DotNet::CesiumForUnity::CesiumIntVec4& v2, const ::DotNet::CesiumForUnity::CesiumIntVec4& v3)
{
    void* reinteropException = nullptr;
    CesiumIntMat4x4 result;
    Construct_1oaleqFQUQx5j2RbOSvw3w(&v0, &v1, &v2, &v3, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::CesiumForUnity::CesiumIntMat4x4::Property_get_Item)(const ::DotNet::CesiumForUnity::CesiumIntMat4x4* thiz, ::std::int32_t index, ::DotNet::CesiumForUnity::CesiumIntVec4* pReturnValue, void** reinteropException) = nullptr;


::DotNet::CesiumForUnity::CesiumIntVec4 CesiumIntMat4x4::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::CesiumForUnity::CesiumIntVec4 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::CesiumForUnity


